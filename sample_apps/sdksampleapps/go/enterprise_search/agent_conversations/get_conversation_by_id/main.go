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

	createRes, err := client.Agents.CreateAgentConversation(ctx, agentKey, components.CreateConversationRequest{
		Query: "Give me a short summary of the latest updates in this agent's knowledge sources.",
	})
	if err != nil {
		log.Fatalf("create conversation: %v", err)
	}
	if createRes == nil || createRes.Object == nil {
		log.Fatal("create conversation: empty response")
	}

	created := createRes.Object.Conversation
	if created.ID == nil || *created.ID == "" {
		log.Fatal("create conversation: missing conversation ID")
	}
	conversationID := *created.ID

	fmt.Println("=== Created Conversation ===")
	fmt.Printf("Conversation ID: %s\n", conversationID)
	if created.Title != nil {
		fmt.Printf("Title:           %s\n", *created.Title)
	}
	if created.Status != nil {
		fmt.Printf("Status:          %s\n", *created.Status)
	}

	getRes, err := client.Agents.GetAgentConversationByID(ctx, operations.GetAgentConversationByIDRequest{
		AgentKey:       agentKey,
		ConversationID: conversationID,
	})
	if err != nil {
		log.Fatalf("get conversation by id: %v", err)
	}
	if getRes == nil || getRes.AgentConversationDetailResponse == nil {
		log.Fatal("get conversation by id: empty response")
	}

	conversation := getRes.AgentConversationDetailResponse.Conversation

	fmt.Println("\n=== Retrieved Conversation ===")
	fmt.Printf("Conversation ID: %s\n", conversation.ID)
	if conversation.Title != nil {
		fmt.Printf("Title:           %s\n", *conversation.Title)
	}
	if conversation.Status != nil {
		fmt.Printf("Status:          %s\n", *conversation.Status)
	}
	fmt.Printf("Created At:      %s\n", conversation.CreatedAt.Format("2006-01-02 15:04:05"))
	fmt.Printf("Messages:        %d\n", len(conversation.Messages))

	for i, message := range conversation.Messages {
		fmt.Printf("\nMessage %d\n", i+1)
		if message.MessageType != nil {
			fmt.Printf("Type:    %s\n", *message.MessageType)
		}
		if message.Content != nil {
			fmt.Printf("Content: %s\n", *message.Content)
		}
	}
}
