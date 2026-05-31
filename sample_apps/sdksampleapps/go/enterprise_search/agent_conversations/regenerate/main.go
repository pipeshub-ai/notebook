package main

import (
	"context"
	"encoding/json"
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

	messageID, originalAnswer, err := lastBotResponse(conv.Messages)
	if err != nil {
		log.Fatalf("find bot response: %v", err)
	}

	fmt.Printf("Agent:         %s\n", agentKey)
	fmt.Printf("Conversation:  %s\n", conversationID)
	fmt.Printf("Message:       %s\n", messageID)
	fmt.Printf("You:           %s\n\n", query)
	fmt.Printf("Original bot response:\n%s\n\n", originalAnswer)

	// regenerateAgentConversationMessage — stream a new answer for the last bot response.
	regenRes, err := client.Agents.RegenerateAgentConversationMessage(ctx, agentKey, conversationID, messageID, nil)
	if err != nil {
		log.Fatalf("regenerate: %v", err)
	}
	if regenRes.AgentRegenerateSSEEvent == nil {
		log.Fatal("regenerate: no SSE stream returned")
	}
	stream := regenRes.AgentRegenerateSSEEvent
	defer stream.Close()

	fmt.Print("Regenerated bot response:\n")

	for stream.Next() {
		ev := stream.Value()
		if ev == nil || ev.Event == nil || ev.Data == nil {
			continue
		}
		switch *ev.Event {
		case components.AgentRegenerateSSEEventEventComplete:
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
		case components.AgentRegenerateSSEEventEventError:
			log.Fatalf("stream error: %s", *ev.Data)
		}
	}
	if err := stream.Err(); err != nil {
		log.Fatalf("stream: %v", err)
	}
}

func lastBotResponse(messages []components.Message) (messageID, content string, err error) {
	for i := len(messages) - 1; i >= 0; i-- {
		m := messages[i]
		if m.MessageType == nil || *m.MessageType != components.MessageMessageTypeBotResponse {
			continue
		}
		if m.ID == nil || *m.ID == "" {
			return "", "", fmt.Errorf("bot response missing message ID")
		}
		if m.Content != nil {
			content = *m.Content
		}
		return *m.ID, content, nil
	}
	return "", "", fmt.Errorf("no bot_response message in conversation")
}
