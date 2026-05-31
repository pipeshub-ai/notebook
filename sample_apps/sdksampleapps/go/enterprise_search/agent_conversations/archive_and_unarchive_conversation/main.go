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
	fmt.Printf("You:          %s\n\n", query)

	// archiveAgentConversation — move the conversation to the archive.
	archiveRes, err := client.Agents.ArchiveAgentConversation(ctx, agentKey, conversationID)
	if err != nil {
		log.Fatalf("archive conversation: %v", err)
	}
	if archiveRes == nil || archiveRes.AgentConversationArchiveResponse == nil {
		log.Fatal("archive conversation: empty response")
	}

	archived := archiveRes.AgentConversationArchiveResponse
	fmt.Println("=== Archived ===")
	fmt.Printf("ID:         %s\n", archived.ID)
	fmt.Printf("Status:     %s\n", archived.Status)
	fmt.Printf("ArchivedBy: %s\n", archived.ArchivedBy)
	fmt.Printf("ArchivedAt: %s\n\n", archived.ArchivedAt.Format("2006-01-02 15:04:05"))

	// unarchiveAgentConversation — restore the conversation to the active list.
	unarchiveRes, err := client.Agents.UnarchiveAgentConversation(ctx, agentKey, conversationID)
	if err != nil {
		log.Fatalf("unarchive conversation: %v", err)
	}
	if unarchiveRes == nil || unarchiveRes.AgentConversationUnarchiveResponse == nil {
		log.Fatal("unarchive conversation: empty response")
	}

	unarchived := unarchiveRes.AgentConversationUnarchiveResponse
	fmt.Println("=== Unarchived ===")
	fmt.Printf("ID:           %s\n", unarchived.ID)
	fmt.Printf("Status:       %s\n", unarchived.Status)
	fmt.Printf("UnarchivedBy: %s\n", unarchived.UnarchivedBy)
	fmt.Printf("UnarchivedAt: %s\n", unarchived.UnarchivedAt.Format("2006-01-02 15:04:05"))
}
