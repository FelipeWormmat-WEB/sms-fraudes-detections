FROM golang:1.26.1-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -o classifier *.go

FROM alpine:3.22
WORKDIR /app
RUN addgroup -S app && adduser -S app -G app
COPY --from=builder /app/classifier .
COPY datasets datasets
COPY model.json model.json
USER app
EXPOSE 8080
CMD ["./classifier"]
