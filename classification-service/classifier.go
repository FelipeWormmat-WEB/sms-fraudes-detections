package main

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

type Classifier struct {
	hamCounts  map[string]int
	spamCounts map[string]int
	hamWords   int
	spamWords  int
	hamDocs    int
	spamDocs   int
	vocab      map[string]struct{}
}

var sepRe = regexp.MustCompile(`[\t,]`)

func NewClassifier() *Classifier {
	return &Classifier{
		hamCounts:  make(map[string]int),
		spamCounts: make(map[string]int),
		vocab:      make(map[string]struct{}),
	}
}
func (c *Classifier) TrainFromDir(dir string) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return fmt.Errorf("read datasets dir: %w", err)
	}
	var trainedFiles int
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		fmt.Printf("[TrainFromDir] Found file: %s\n", name) // Log do arquivo encontrado
		if !strings.HasSuffix(strings.ToLower(name), ".csv") {
			fmt.Printf("[TrainFromDir] Skipping non-CSV file: %s\n", name)
			continue
		}
		fp := filepath.Join(dir, name)
		fmt.Printf("[TrainFromDir] Training from file: %s\n", fp)
		f, err := os.Open(fp)
		if err != nil {
			fmt.Printf("[TrainFromDir] Error opening %s: %v\n", fp, err)
			continue
		}
		if err := c.TrainFromReader(f); err != nil {
			fmt.Printf("[TrainFromDir] Error training from %s: %v\n", fp, err)
		}
		_ = f.Close()
		trainedFiles++
	}
	fmt.Printf("[TrainFromDir] Training summary: files=%d hamDocs=%d spamDocs=%d vocab=%d\n",
		trainedFiles, c.hamDocs, c.spamDocs, len(c.vocab))
	if trainedFiles == 0 {
		return errors.New("no CSV files found to train")
	}
	return nil
}

func (c *Classifier) TrainFromReader(r io.Reader) error {
	s := bufio.NewScanner(r)
	lineNum := 0
	for s.Scan() {
		lineNum++
		line := s.Text()
		label, text, ok := parseLabelText(line)
		if !ok {
			log.Printf("[TrainFromReader] Line %d: invalid format: %s\n", lineNum, line)
			continue
		}
		log.Printf("[TrainFromReader] Line %d: label=%s text=%s\n", lineNum, label, text)
		c.train(label, text)
	}
	return s.Err()
}

func (c *Classifier) train(label string, text string) {
	words := tokenize(text)
	if len(words) == 0 {
		log.Printf("[train] Empty words for label=%s text=%s\n", label, text)
		return
	}
	switch strings.ToLower(label) {
	case "spam":
		c.spamDocs++
		for _, w := range words {
			c.spamCounts[w]++
			c.spamWords++
			c.vocab[w] = struct{}{}
			log.Printf("[train] Spam word: %s (count=%d)\n", w, c.spamCounts[w])
		}
	case "ham":
		c.hamDocs++
		for _, w := range words {
			c.hamCounts[w]++
			c.hamWords++
			c.vocab[w] = struct{}{}
			log.Printf("[train] Ham word: %s (count=%d)\n", w, c.hamCounts[w])
		}
	default:
		log.Printf("[train] Unknown label: %s\n", label)
	}
}

func (c *Classifier) Predict(text string) (string, float64) {
	words := tokenize(text)
	if len(words) == 0 {
		fmt.Println("[Predict] No words found in text.")
		return "ham", 0.5
	}
	V := float64(len(c.vocab))
	if V == 0 {
		fmt.Println("[Predict] Vocabulary size is zero.")
		return "unknown", 0.0
	}
	totalDocs := float64(c.hamDocs + c.spamDocs)
	priorHam := math.Log((float64(c.hamDocs) + 1.0) / (totalDocs + 2.0))
	priorSpam := math.Log((float64(c.spamDocs) + 1.0) / (totalDocs + 2.0))
	logHam := priorHam
	logSpam := priorSpam
	fmt.Printf("[Predict] Initial logHam: %f, logSpam: %f\n", logHam, logSpam)
	for _, w := range words {
		cwHam := float64(c.hamCounts[w])
		cwSpam := float64(c.spamCounts[w])
		if c.hamWords > 0 {
			logHam += math.Log((cwHam + 1.0) / (float64(c.hamWords) + V))
		}
		if c.spamWords > 0 {
			logSpam += math.Log((cwSpam + 1.0) / (float64(c.spamWords) + V))
		}
		fmt.Printf("[Predict] Word: %s, cwHam: %f, cwSpam: %f, logHam: %f, logSpam: %f\n", w, cwHam, cwSpam, logHam, logSpam)
	}
	m := math.Max(logHam, logSpam)
	eh := math.Exp(logHam - m)
	es := math.Exp(logSpam - m)
	sum := eh + es
	fmt.Printf("[Predict] eh: %f, es: %f, sum: %f\n", eh, es, sum)
	if sum == 0 {
		fmt.Println("[Predict] Sum of exponentials is zero.")
		return "unknown", 0.0
	}
	ph := eh / sum
	ps := es / sum
	fmt.Printf("[Predict] ph: %f, ps: %f\n", ph, ps)
	if ps >= ph {
		return "spam", ps
	}
	return "ham", ph
}

func parseLabelText(line string) (string, string, bool) {
	line = strings.TrimSpace(line)
	if line == "" {
		return "", "", false
	}

	// Divide a linha por tabulação
	parts := strings.SplitN(line, "\t", 2)
	if len(parts) < 2 {
		return "", "", false
	}

	label := strings.ToLower(strings.TrimSpace(parts[0]))
	text := strings.TrimSpace(parts[1])

	if label == "spam" || label == "ham" {
		return label, text, true
	}
	return "", "", false
}

func tokenize(text string) []string {
	text = strings.ToLower(text)
	var b strings.Builder
	b.Grow(len(text))
	for _, r := range text {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == 'á' || r == 'é' || r == 'í' || r == 'ó' || r == 'ú' || r == 'ã' || r == 'õ' || r == 'â' || r == 'ê' || r == 'ô' || r == 'ç' {
			b.WriteRune(r)
		} else {
			b.WriteByte(' ')
		}
	}
	parts := strings.Fields(b.String())
	return parts
}

func (c *Classifier) LoadModel(modelPath string) error {
	file, err := os.Open(modelPath)
	if err != nil {
		return fmt.Errorf("failed to open model file: %w", err)
	}
	defer file.Close()

	decoder := json.NewDecoder(file)
	if err := decoder.Decode(c); err != nil {
		return fmt.Errorf("failed to decode model: %w", err)
	}

	fmt.Println("[LoadModel] Model loaded successfully.")
	return nil
}

func (c *Classifier) SaveModel(modelPath string) error {
	file, err := os.Create(modelPath)
	if err != nil {
		return fmt.Errorf("failed to create model file: %w", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	if err := encoder.Encode(c); err != nil {
		return fmt.Errorf("failed to encode model: %w", err)
	}

	fmt.Println("[SaveModel] Model saved successfully.")
	return nil
}
