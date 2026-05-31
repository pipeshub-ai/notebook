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

const modelKey = "a95c01365-a7d7-4930-88d5-c936c7d722c5"
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

	// ─── Find connector for conversation ───

	connectorID, err := findConnectorIDByName(ctx, client, connectorName)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Using connector: %s\n\n", connectorID)

	// ─── Create 2 agents ───

	agentKey1, err := createAgent(ctx, client, "SDK Test Agent 1", modelKey, connectorID)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created agent 1: %s\n", agentKey1)
	defer client.Agents.DeleteAgent(ctx, agentKey1)

	agentKey2, err := createAgent(ctx, client, "SDK Test Agent 2", modelKey, connectorID)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Created agent 2: %s\n", agentKey2)
	defer client.Agents.DeleteAgent(ctx, agentKey2)

	// ─── Create multiple conversations on each agent ───

	fmt.Println("\nCreating conversations...")

	convIDs1 := make([]string, 0, 2)
	convIDs2 := make([]string, 0, 2)

	for i, q := range []string{
		"What are the latest tech news?",
		"Tell me about AI advancements",
	} {
		convID, err := streamConversation(ctx, client, agentKey1, q, connectorID)
		if err != nil {
			log.Fatalf("create conversation on agent 1 (%d): %v", i+1, err)
		}
		fmt.Printf("Agent 1 — conversation %d: %s\n", i+1, convID)
		convIDs1 = append(convIDs1, convID)
	}

	for i, q := range []string{
		"What are the latest sports news?",
		"Who won the championship last year?",
	} {
		convID, err := streamConversation(ctx, client, agentKey2, q, connectorID)
		if err != nil {
			log.Fatalf("create conversation on agent 2 (%d): %v", i+1, err)
		}
		fmt.Printf("Agent 2 — conversation %d: %s\n", i+1, convID)
		convIDs2 = append(convIDs2, convID)
	}

	// ─── Archive all conversations ───

	fmt.Println("\nArchiving conversations...")

	for i, convID := range convIDs1 {
		archiveRes, err := client.Agents.ArchiveAgentConversation(ctx, agentKey1, convID)
		if err != nil {
			log.Fatalf("archive agent 1 conversation %d: %v", i+1, err)
		}
		if archiveRes == nil || archiveRes.AgentConversationArchiveResponse == nil {
			log.Fatalf("archive agent 1 conversation %d: empty response", i+1)
		}
		a := archiveRes.AgentConversationArchiveResponse
		fmt.Printf("Archived agent 1 conversation %d: ID=%s, Status=%s\n", i+1, a.ID, a.Status)
	}

	for i, convID := range convIDs2 {
		archiveRes, err := client.Agents.ArchiveAgentConversation(ctx, agentKey2, convID)
		if err != nil {
			log.Fatalf("archive agent 2 conversation %d: %v", i+1, err)
		}
		if archiveRes == nil || archiveRes.AgentConversationArchiveResponse == nil {
			log.Fatalf("archive agent 2 conversation %d: empty response", i+1)
		}
		a := archiveRes.AgentConversationArchiveResponse
		fmt.Printf("Archived agent 2 conversation %d: ID=%s, Status=%s\n", i+1, a.ID, a.Status)
	}

	// ─── List archived conversations grouped by agent ───

	fmt.Println("\n=== Archived Conversations Grouped by Agent ===")

	page := int64(1)
	limit := int64(10)

	listRes, err := client.Agents.ListAgentArchivedConversationsGrouped(ctx, &page, &limit)
	if err != nil {
		log.Fatalf("list archived grouped: %v", err)
	}
	if listRes == nil || listRes.AgentArchivedGroupsResponse == nil {
		log.Fatal("list archived grouped: empty response")
	}

	groups := listRes.AgentArchivedGroupsResponse.Groups
	pagination := listRes.AgentArchivedGroupsResponse.AgentPagination

	for i, g := range groups {
		fmt.Printf("\nGroup %d:\n", i+1)
		fmt.Printf("  Agent Key: %s\n", g.AgentKey)
		fmt.Printf("  Conversations:\n")
		for j, c := range g.Conversations {
			fmt.Printf("    %d. ", j+1)
			if c.ID != nil {
				fmt.Printf("ID: %s", *c.ID)
			}
			if c.Title != nil {
				fmt.Printf(" | Title: %s", *c.Title)
			}
			if c.Status != nil {
				fmt.Printf(" | Status: %s", *c.Status)
			}
			if c.ArchivedAt != nil {
				fmt.Printf(" | Archived: %s", c.ArchivedAt.Format("2006-01-02 15:04"))
			}
			fmt.Println()
		}
	}

	fmt.Printf("\nPagination: Page %d/%d, Total: %d groups\n",
		pagination.Page, pagination.TotalPages, pagination.TotalCount)
}

func createAgent(ctx context.Context, sdk *pipeshub.SDK, name, modelKey, connectorID string) (string, error) {
	createRes, err := sdk.Agents.CreateAgent(ctx, components.AgentCreateRequest{
		Name: name,
		Models: []components.AgentCreateModelEntryUnion{
			components.CreateAgentCreateModelEntryUnionAgentCreateModelEntry(
				components.AgentCreateModelEntry{
					ModelKey:    modelKey,
					IsReasoning: pipeshub.Bool(true),
				},
			),
		},
		Knowledge: []components.AgentCreateKnowledge{
			{
				ConnectorID: connectorID,
			},
		},
	})
	if err != nil {
		return "", fmt.Errorf("create agent: %w", err)
	}
	if createRes == nil || createRes.AgentCreateResponse == nil {
		return "", fmt.Errorf("create agent: empty response")
	}
	return createRes.AgentCreateResponse.Agent.Key, nil
}

func streamConversation(ctx context.Context, sdk *pipeshub.SDK, agentKey, query, connectorID string) (string, error) {
	res, err := sdk.Agents.StreamAgentConversation(ctx, agentKey, components.AgentStreamCreateConversationRequest{
		Query:   query,
		Filters: &components.Filters{Apps: []string{connectorID}},
	})
	if err != nil {
		return "", fmt.Errorf("stream conversation: %w", err)
	}
	if res.AgentStreamSSEEvent == nil {
		return "", fmt.Errorf("stream conversation: no SSE stream returned")
	}
	stream := res.AgentStreamSSEEvent
	defer stream.Close()

	for stream.Next() {
		ev := stream.Value()
		if ev == nil || ev.Event == nil || ev.Data == nil {
			continue
		}
		switch *ev.Event {
		case components.AgentStreamSSEEventEventComplete:
			var payload struct {
				Conversation struct {
					ID string `json:"_id"`
				} `json:"conversation"`
			}
			if err := json.Unmarshal([]byte(*ev.Data), &payload); err != nil {
				return "", fmt.Errorf("decode complete: %w", err)
			}
			if payload.Conversation.ID == "" {
				return "", fmt.Errorf("conversation ID not found in complete event")
			}
			return payload.Conversation.ID, nil
		case components.AgentStreamSSEEventEventError:
			return "", fmt.Errorf("stream error: %s", *ev.Data)
		}
	}
	if err := stream.Err(); err != nil {
		return "", fmt.Errorf("stream: %w", err)
	}
	return "", fmt.Errorf("stream ended without complete event")
}

func findConnectorIDByName(ctx context.Context, sdk *pipeshub.SDK, name string) (string, error) {
	res, err := sdk.KnowledgeHub.GetKnowledgeHubRootNodes(ctx, operations.GetKnowledgeHubRootNodesRequest{})
	if err != nil {
		return "", fmt.Errorf("get knowledge hub root nodes: %w", err)
	}
	if res == nil || res.KnowledgeHubNodesResponse == nil {
		return "", fmt.Errorf("get knowledge hub root nodes: empty response")
	}

	for _, n := range res.KnowledgeHubNodesResponse.GetItems() {
		if n.Name == name && n.Origin == components.KnowledgeHubNodeOriginConnector {
			return n.ID, nil
		}
	}

	return "", fmt.Errorf("connector %q not found", name)
}