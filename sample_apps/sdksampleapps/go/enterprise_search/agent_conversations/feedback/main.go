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

	messageID, botAnswer, err := lastBotResponse(conv.Messages)
	if err != nil {
		log.Fatalf("find bot response: %v", err)
	}

	fmt.Printf("Agent:         %s\n", agentKey)
	fmt.Printf("Conversation:  %s\n", conversationID)
	fmt.Printf("Message:       %s\n", messageID)
	fmt.Printf("You:           %s\n\n", query)
	fmt.Printf("Bot response:\n%s\n\n", botAnswer)

	// updateAgentConversationMessageFeedback — submit feedback on the bot response.
	isHelpful := true
	accuracy := int64(4)
	relevance := int64(5)
	completeness := int64(4)
	clarity := int64(5)
	positive := "Clear and helpful overview of the agent's capabilities."

	feedbackRes, err := client.Agents.UpdateAgentConversationMessageFeedback(
		ctx,
		agentKey,
		conversationID,
		messageID,
		components.MessageFeedback{
			IsHelpful: &isHelpful,
			Ratings: &components.Ratings{
				Accuracy:     &accuracy,
				Relevance:    &relevance,
				Completeness: &completeness,
				Clarity:      &clarity,
			},
			Categories: []components.MessageFeedbackCategory{
				components.MessageFeedbackCategoryWellExplained,
			},
			Comments: &components.Comments{
				Positive: &positive,
			},
		},
	)
	if err != nil {
		log.Fatalf("submit feedback: %v", err)
	}
	if feedbackRes == nil || feedbackRes.Object == nil {
		log.Fatal("submit feedback: empty response")
	}

	out, err := json.MarshalIndent(feedbackRes.Object, "", "  ")
	if err != nil {
		log.Fatalf("encode feedback response: %v", err)
	}

	fmt.Println("Feedback submitted:")
	fmt.Println(string(out))
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
