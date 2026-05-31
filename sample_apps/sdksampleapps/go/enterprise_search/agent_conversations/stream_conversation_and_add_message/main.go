package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	pipeshub "github.com/pipeshub-ai/pipeshub-sdk-go"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/components"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/operations"

	"enterprise_search/auth"
)

const agentKey = "e6f848ca-e2ab-4594-9925-e1136629f474"
const connectorName = "ABC News RSS"

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

	// ─── Find an existing conversation ───

	conversationID, err := findFirstConversation(ctx, client)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Using conversation: %s\n\n", conversationID)

	// ─── Send a follow-up message to the existing conversation ───

	query := "Can you give me more details on that?"

	res, err := client.Agents.StreamAgentConversationMessage(ctx, agentKey, conversationID, components.AgentAddMessageStreamRequest{
		Query: query,
	})
	if err != nil {
		log.Fatalf("stream message: %v", err)
	}
	if res.AgentMessageStreamSSEEvent == nil {
		log.Fatal("no SSE stream returned")
	}
	stream := res.AgentMessageStreamSSEEvent
	defer stream.Close()

	fmt.Printf("You: %s\n\nBot: ", query)

	for stream.Next() {
		ev := stream.Value()
		if ev == nil || ev.Event == nil || ev.Data == nil {
			continue
		}
		switch *ev.Event {
		case components.AgentMessageStreamSSEEventEventComplete:
			var payload struct {
				Conversation struct {
					Messages []struct {
						MessageType string `json:"messageType"`
						Content     string `json:"content"`
					} `json:"messages"`
				} `json:"conversation"`
			}
			if err := json.Unmarshal([]byte(*ev.Data), &payload); err != nil {
				log.Fatalf("decode complete: %v", err)
			}
			for _, m := range payload.Conversation.Messages {
				if m.MessageType == "bot_response" {
					fmt.Println(m.Content)
					return
				}
			}
			log.Fatal("no bot response in complete event")
		case components.AgentMessageStreamSSEEventEventError:
			log.Fatalf("stream error: %s", *ev.Data)
		}
	}
	if err := stream.Err(); err != nil {
		log.Fatalf("stream: %v", err)
	}
}

func findFirstConversation(ctx context.Context, sdk *pipeshub.SDK) (string, error) {
	res, err := sdk.Agents.ListAgentConversations(ctx, operations.ListAgentConversationsRequest{
		AgentKey: agentKey,
	})
	if err != nil {
		return "", fmt.Errorf("list conversations: %w", err)
	}
	if res == nil || res.AgentConversationListResponse == nil {
		return "", fmt.Errorf("list conversations: empty response")
	}

	convs := res.AgentConversationListResponse.Conversations
	if len(convs) == 0 {
		return "", fmt.Errorf("no conversations found for agent %s", agentKey)
	}
	if convs[0].ID == nil {
		return "", fmt.Errorf("first conversation has no ID")
	}
	return *convs[0].ID, nil
}