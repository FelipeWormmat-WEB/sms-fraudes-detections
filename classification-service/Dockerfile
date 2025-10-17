FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN go mod tidy
RUN go build -o classifier *.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/classifier .
COPY datasets datasets
COPY model.json model.json
EXPOSE 8080
CMD ["./classifier"]
