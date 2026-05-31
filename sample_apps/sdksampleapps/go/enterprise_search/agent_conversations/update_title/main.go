package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/components"

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
	query := "What can you help me with?"
	newTitle := "SDK Title Update Example"

	// createAgentConversation — start a new conversation with the agent.
	createRes, err := client.Agents.CreateAgentConversation(ctx, agentKey, components.CreateConversationRequest{
		Query: query,
	})
	if err != nil {
		log.Fatalf("create conversation: %v", err)
	}
	if createRes == nil || createRes.Object == nil {
		log.Fatal("create conversation: empty response")
	}

	conv := createRes.Object.Conversation
	if conv.ID == nil || *conv.ID == "" {
		log.Fatal("create conversation: missing conversation ID")
	}
	conversationID := *conv.ID

	fmt.Printf("Agent:        %s\n", agentKey)
	fmt.Printf("Conversation: %s\n", conversationID)
	fmt.Printf("You:          %s\n", query)
	if conv.Title != nil {
		fmt.Printf("Original title: %s\n\n", *conv.Title)
	} else {
		fmt.Println("Original title: (none)")
		fmt.Println()
	}

	// updateAgentConversationTitle — rename the conversation.
	updateRes, err := client.Agents.UpdateAgentConversationTitle(
		ctx,
		agentKey,
		conversationID,
		components.ConversationTitleUpdateRequest{
			Title: newTitle,
		},
	)
	if err != nil {
		log.Fatalf("update title: %v", err)
	}
	if updateRes == nil || updateRes.AgentConversationTitleUpdateResponse == nil {
		log.Fatal("update title: empty response")
	}

	updated := updateRes.AgentConversationTitleUpdateResponse.Conversation

	fmt.Println("=== Title Updated ===")
	if updated.ID != nil {
		fmt.Printf("Conversation: %s\n", *updated.ID)
	}
	if updated.Title != nil {
		fmt.Printf("New title:    %s\n", *updated.Title)
	}
	if updated.Status != nil {
		fmt.Printf("Status:       %s\n", *updated.Status)
	}
	if updated.UpdatedAt != nil {
		fmt.Printf("Updated at:   %s\n", updated.UpdatedAt.Format("2006-01-02 15:04:05"))
	}
}
