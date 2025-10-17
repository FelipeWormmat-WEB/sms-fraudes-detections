package main

import (
	"log"
	"net/http"

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

	r.POST("/classify", func(c *gin.Context) {
		var req Request
		if err := c.ShouldBindJSON(&req); err != nil {
			log.Printf("[classifier] bad request: %v", err)
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		label, conf := clf.Predict(req.Message)
		pred := label
		if label == "ham" {
			pred = "legítimo"
		}
		log.Printf("[classifier] /classify len=%d label=%s conf=%.3f", len(req.Message), pred, conf)
		res := Response{
			Message:    req.Message,
			Prediction: pred,
			Confidence: conf,
		}
		c.JSON(http.StatusOK, res)
	})
	r.POST("/retrain", func(c *gin.Context) {
		datasetsDir := "./datasets"
		if err := clf.TrainFromDir(datasetsDir); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
		if err := clf.SaveModel("model.json"); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
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
