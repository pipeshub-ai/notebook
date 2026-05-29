package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/operations"

	"enterprise_search/auth"
)

const agentKey = "e6f848ca-e2ab-4594-9925-e1136629f474"

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

	// ─── List agent conversations ───

	listRes, err := client.Agents.ListAgentConversations(ctx, operations.ListAgentConversationsRequest{
		AgentKey: agentKey,
	})
	if err != nil {
		log.Fatalf("list conversations: %v", err)
	}
	if listRes == nil || listRes.AgentConversationListResponse == nil {
		log.Fatal("list conversations: empty response")
	}

	convs := listRes.AgentConversationListResponse.Conversations
	fmt.Printf("=== %d Conversations ===\n", len(convs))
	for i, c := range convs {
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
		if c.Initiator != nil {
			fmt.Printf("  Initiator: %s\n", *c.Initiator)
		}
		if c.CreatedAt != nil {
			fmt.Printf("  Created:   %s\n", c.CreatedAt.Format("2006-01-02 15:04"))
		}
	}

	// ─── Get one conversation by ID ───

	if len(convs) == 0 {
		log.Fatal("no conversations found")
	}
	if convs[0].ID == nil {
		log.Fatal("first conversation has no ID")
	}
	firstConvID := *convs[0].ID

	getRes, err := client.Agents.GetAgentConversationByID(ctx, operations.GetAgentConversationByIDRequest{
		AgentKey:       agentKey,
		ConversationID: firstConvID,
	})
	if err != nil {
		log.Fatalf("get conversation: %v", err)
	}
	if getRes == nil || getRes.AgentConversationDetailResponse == nil {
		log.Fatal("get conversation: empty response")
	}

	c := getRes.AgentConversationDetailResponse.Conversation

	fmt.Println("\n=== Conversation Detail ===")
	if c.Title != nil {
		fmt.Printf("Title:    %s\n", *c.Title)
	}
	fmt.Printf("ID:       %s\n", c.ID)
	if c.Status != nil {
		fmt.Printf("Status:   %s\n", *c.Status)
	}
	fmt.Printf("Created:  %s\n", c.CreatedAt.Format("2006-01-02 15:04"))
	fmt.Printf("Shared:   %v\n", c.IsShared)

	fmt.Println("\n--- Messages ---")
	for i, m := range c.Messages {
		fmt.Printf("\n[%d] ", i+1)
		if m.MessageType != nil {
			fmt.Printf("(%s)", *m.MessageType)
		}
		if m.Content != nil {
			fmt.Println()
			fmt.Println(*m.Content)
		} else {
			fmt.Println()
		}
	}
}
