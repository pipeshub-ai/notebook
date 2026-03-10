package main

import (
	"context"
	"fmt"
	"log"
	"os"

	pipeshub "github.com/pipeshub-ai/pipeshub-sdk-go"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/components"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/operations"
)

func main() {
	token := os.Getenv("PIPESHUB_BEARER_AUTH")
	if token == "" {
		log.Fatal("PIPESHUB_BEARER_AUTH environment variable is required")
	}

	serverURL := os.Getenv("PIPESHUB_SERVER_URL")
	if serverURL == "" {
		serverURL = "https://app.pipeshub.com/api/v1"
	}

	// Initialize the PipesHub SDK client
	client := pipeshub.New(
		pipeshub.WithSecurity(components.Security{
			BearerAuth: pipeshub.String(token),
		}),
		pipeshub.WithServerURL(serverURL),
	)

	ctx := context.Background()

	// Step 1: List knowledge bases to find a target KB
	fmt.Println("Listing knowledge bases...")
	listRes, err := client.KnowledgeBases.List(ctx, operations.ListKnowledgeBasesRequest{})
	if err != nil {
		log.Fatalf("Failed to list knowledge bases: %v", err)
	}

	if listRes.Object == nil || len(listRes.Object.KnowledgeBases) == 0 {
		log.Fatal("No knowledge bases found. Please create one first.")
	}

	// Use the first knowledge base
	kb := listRes.Object.KnowledgeBases[0]
	fmt.Printf("Using knowledge base: %s (ID: %s)\n", kb.Name, *kb.ID)

	// Step 2: Upload a file
	filePath := "sample.txt"
	if len(os.Args) > 1 {
		filePath = os.Args[1]
	}

	fileData, err := os.ReadFile(filePath)
	if err != nil {
		log.Fatalf("Failed to read file %s: %v", filePath, err)
	}

	fmt.Printf("Uploading file: %s (%d bytes)\n", filePath, len(fileData))

	uploadRes, err := client.Upload.Files(ctx, *kb.ID, operations.UploadRecordsToKBRequestBody{
		Files: []operations.UploadRecordsToKBFile{
			{
				FileName: filePath,
				Content:  fileData,
			},
		},
	})
	if err != nil {
		log.Fatalf("Failed to upload file: %v", err)
	}

	// Step 3: Print results
	if uploadRes.UploadResult != nil {
		fmt.Printf("Upload message: %s\n", *uploadRes.UploadResult.Message)
		for _, result := range uploadRes.UploadResult.UploadResults {
			fmt.Printf("  - %s: status=%s, recordId=%s\n",
				*result.RecordName, *result.Status, *result.RecordID)
		}
	}

	fmt.Println("Done!")
}
