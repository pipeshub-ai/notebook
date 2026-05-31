package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	pipeshub "github.com/pipeshub-ai/pipeshub-sdk-go"
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

	owned, shared, err := listAllConversations(ctx, client, agentKey)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("Agent: %s\n\n", agentKey)
	fmt.Printf("=== %d Owned Conversations ===\n", len(owned))
	for i, c := range owned {
		printConversation(i+1, c)
	}

	fmt.Printf("\n=== %d Shared With Me ===\n", len(shared))
	for i, c := range shared {
		printConversation(i+1, c)
	}
}

func listAllConversations(
	ctx context.Context,
	client *pipeshub.SDK,
	agentKey string,
) ([]components.AgentConversationListItem, []components.AgentConversationListItem, error) {
	limit := int64(100)
	page := int64(1)
	var owned, shared []components.AgentConversationListItem

	for {
		res, err := client.Agents.ListAgentConversations(ctx, operations.ListAgentConversationsRequest{
			AgentKey: agentKey,
			Page:     &page,
			Limit:    &limit,
		})
		if err != nil {
			return nil, nil, fmt.Errorf("list conversations (page %d): %w", page, err)
		}
		if res == nil || res.AgentConversationListResponse == nil {
			return nil, nil, fmt.Errorf("list conversations (page %d): empty response", page)
		}

		body := res.AgentConversationListResponse
		owned = append(owned, body.Conversations...)
		if page == 1 {
			shared = append(shared, body.SharedWithMeConversations...)
		}

		if !body.Pagination.HasNextPage {
			break
		}
		page++
	}

	return owned, shared, nil
}

func printConversation(index int, c components.AgentConversationListItem) {
	fmt.Printf("\n%d.", index)
	if c.ID != nil {
		fmt.Printf("  ID:        %s\n", *c.ID)
	}
	if c.Title != nil {
		fmt.Printf("  Title:     %s\n", *c.Title)
	}
	if c.Status != nil {
		fmt.Printf("  Status:    %s\n", *c.Status)
	}
	if c.Initiator != nil {
		fmt.Printf("  Initiator: %s\n", *c.Initiator)
	}
	if c.CreatedAt != nil {
		fmt.Printf("  Created:   %s\n", c.CreatedAt.Format("2006-01-02 15:04"))
	}
}
