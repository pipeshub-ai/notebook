package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/components"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/operations"

	"enterprise_search/auth"
)

const agentKey = "02a7d998-d21b-4015-aaf7-5cda765c1012"

func main() {
	if len(os.Args) < 2 {
		log.Fatal("usage: go run . <path-to-.env>")
	}
	if err := godotenv.Load(os.Args[1]); err != nil {
		log.Fatalf("load .env: %v", err)
	}

	client, err := auth.NewClient(
		os.Getenv("PIPESHUB_TEST_USER_EMAIL"),
		os.Getenv("PIPESHUB_TEST_USER_PASSWORD"),
	)
	if err != nil {
		log.Fatal(err)
	}

	ctx := context.Background()
	queries := []string{
		"What can you help me with?",
		"Summarize your main capabilities in one paragraph.",
	}

	fmt.Printf("Agent: %s\n\n", agentKey)

	var conversationIDs []string

	for i, query := range queries {
		createRes, err := client.Agents.CreateAgentConversation(ctx, agentKey, components.CreateConversationRequest{
			Query: query,
		})
		if err != nil {
			log.Fatalf("create conversation %d: %v", i+1, err)
		}
		if createRes == nil || createRes.Object == nil {
			log.Fatalf("create conversation %d: empty response", i+1)
		}

		conv := createRes.Object.Conversation
		if conv.ID == nil || *conv.ID == "" {
			log.Fatalf("create conversation %d: missing conversation ID", i+1)
		}

		conversationIDs = append(conversationIDs, *conv.ID)
		fmt.Printf("Created conversation %d: %s\n", i+1, *conv.ID)
		fmt.Printf("  Query: %s\n", query)
	}

	fmt.Println("\nArchiving conversations...")
	for i, conversationID := range conversationIDs {
		archiveRes, err := client.Agents.ArchiveAgentConversation(ctx, agentKey, conversationID)
		if err != nil {
			log.Fatalf("archive conversation %d: %v", i+1, err)
		}
		if archiveRes == nil || archiveRes.AgentConversationArchiveResponse == nil {
			log.Fatalf("archive conversation %d: empty response", i+1)
		}

		archived := archiveRes.AgentConversationArchiveResponse
		fmt.Printf("Archived conversation %d: %s (status=%s)\n", i+1, archived.ID, archived.Status)
	}

	limit := int64(100)
	page := int64(1)

	listRes, err := client.Agents.ListAgentConversationArchives(ctx, operations.ListAgentConversationArchivesRequest{
		AgentKey: agentKey,
		Page:     &page,
		Limit:    &limit,
	})
	if err != nil {
		log.Fatalf("list archived conversations: %v", err)
	}
	if listRes == nil || listRes.AgentArchivedConversationListResponse == nil {
		log.Fatal("list archived conversations: empty response")
	}

	body := listRes.AgentArchivedConversationListResponse
	fmt.Printf("\n=== Archived Conversations (%d on page, %d total) ===\n",
		len(body.Conversations),
		body.Pagination.TotalCount,
	)

	for i, c := range body.Conversations {
		fmt.Printf("\n%d.", i+1)
		if c.ID != nil {
			fmt.Printf("  ID:        %s\n", *c.ID)
		}
		if c.Title != nil {
			fmt.Printf("  Title:     %s\n", *c.Title)
		}
		if c.Status != nil {
			fmt.Printf("  Status:    %s\n", *c.Status)
		}
		if c.IsArchived != nil {
			fmt.Printf("  Archived:  %v\n", *c.IsArchived)
		}
		if c.ArchivedAt != nil {
			fmt.Printf("  ArchivedAt:%s\n", c.ArchivedAt.Format("2006-01-02 15:04"))
		}
	}
}
