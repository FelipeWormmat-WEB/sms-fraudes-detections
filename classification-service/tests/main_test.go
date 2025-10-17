package tests

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

func TestClassify(t *testing.T) {
	router := gin.Default()
	router.POST("/classify", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"prediction": "legítimo"})
	})

	w := httptest.NewRecorder()
	body := bytes.NewBufferString(`{"message":"teste"}`)
	req, _ := http.NewRequest("POST", "/classify", body)
	req.Header.Set("Content-Type", "application/json")

	router.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("Esperado 200, obtido %d", w.Code)
	}
}
