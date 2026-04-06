package main

import (
	"crypto/subtle"
	"log"
	"net/http"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
)

type Request struct {
	Message string `json:"message"`
}

type Response struct {
	Message    string  `json:"message"`
	Prediction string  `json:"prediction"`
	Confidence float64 `json:"confidence"`
}

func requireInternalToken() gin.HandlerFunc {
	expectedToken := strings.TrimSpace(os.Getenv("INTERNAL_SERVICE_TOKEN"))
	return func(c *gin.Context) {
		if expectedToken == "" {
			c.AbortWithStatusJSON(http.StatusServiceUnavailable, gin.H{"error": "internal service token not configured"})
			return
		}

		providedToken := strings.TrimSpace(c.GetHeader("X-Internal-Service-Token"))
		if len(providedToken) != len(expectedToken) ||
			subtle.ConstantTimeCompare([]byte(providedToken), []byte(expectedToken)) != 1 {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		c.Next()
	}
}

func retrainEnabled() bool {
	return strings.EqualFold(strings.TrimSpace(os.Getenv("ENABLE_RETRAIN")), "true")
}

func main() {
	log.Printf("[classifier] starting service")
	clf := NewClassifier()

	// Forçar treinamento e salvar o modelo
	datasetsDir := "./datasets"
	if err := clf.TrainFromDir(datasetsDir); err != nil {
		log.Fatalf("[classifier] training failed: %v", err)
	} else {
		if err := clf.SaveModel("model.json"); err != nil {
			log.Fatalf("[classifier] ERROR saving model: %v", err)
		} else {
			log.Printf("[classifier] model saved to model.json")
		}
	}

	r := gin.Default()

	// Health endpoints for quick checks
	r.GET("/", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "ok"}) })
	r.GET("/health", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"status": "healthy"}) })
	// Helpful hint for GET /classify
	r.GET("/classify", func(c *gin.Context) {
		c.JSON(http.StatusMethodNotAllowed, gin.H{"detail": "use POST /classify with JSON {\"message\": \"...\"}"})
	})

	r.POST("/classify", requireInternalToken(), func(c *gin.Context) {
		var req Request
		if err := c.ShouldBindJSON(&req); err != nil {
			log.Printf("[classifier] bad request: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid request payload"})
			return
		}
		if trimmed := strings.TrimSpace(req.Message); trimmed == "" || len(trimmed) > 4096 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "message must be between 1 and 4096 characters"})
			return
		}

		label, conf := clf.Predict(req.Message)
		pred := label
		log.Printf("[classifier] /classify len=%d label=%s conf=%.3f", len(req.Message), pred, conf)
		res := Response{
			Message:    req.Message,
			Prediction: pred,
			Confidence: conf,
		}
		c.JSON(http.StatusOK, res)
	})
	r.POST("/retrain", requireInternalToken(), func(c *gin.Context) {
		if !retrainEnabled() {
			c.JSON(http.StatusNotFound, gin.H{"error": "not found"})
			return
		}
		datasetsDir := "./datasets"
		if err := clf.TrainFromDir(datasetsDir); err != nil {
			log.Printf("[classifier] retraining failed: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "retraining failed"})
			return
		}
		if err := clf.SaveModel("model.json"); err != nil {
			log.Printf("[classifier] model save failed: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "model persistence failed"})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"status":    "retrained",
			"hamDocs":   clf.hamDocs,
			"spamDocs":  clf.spamDocs,
			"vocabSize": len(clf.vocab),
		})
	})

	log.Printf("[classifier] server listening on :8080")
	if err := r.Run(":8080"); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
