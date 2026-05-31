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

const modelKey = "f1ffcb38-5fa4-4d77-ac70-8ca8af08be7c"

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

	// ─── Find connector and knowledge base IDs ───

	connectorID, connectorName, err := findFirstConnector(ctx, client)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Using connector: %s (%s)\n", connectorName, connectorID)

	kbID, kbName, err := findFirstKnowledgeBase(ctx, client)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Using knowledge base: %s (%s)\n", kbName, kbID)

	// ─── Create agent ───

	knowledgeFilters := components.CreateAgentCreateKnowledgeFiltersAgentKnowledgeFiltersParsed(
		components.AgentKnowledgeFiltersParsed{
			RecordGroups: []string{kbID},
		},
	)

	createRes, err := client.Agents.CreateAgent(ctx, components.AgentCreateRequest{
		Name: "SDK Test Agent",
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
				Filters:     &knowledgeFilters,
			},
		},
	})
	if err != nil {
		log.Fatalf("create agent: %v", err)
	}
	if createRes == nil || createRes.AgentCreateResponse == nil {
		log.Fatal("create agent: empty response")
	}

	agent := createRes.AgentCreateResponse.Agent
	fmt.Println("\n=== Created Agent ===")
	fmt.Printf("Name:  %s\n", agent.Name)
	fmt.Printf("Key:   %s\n", agent.Key)

	// ─── Update agent ───

	updateRes, err := client.Agents.UpdateAgent(ctx, agent.Key, components.AgentUpdateRequest{
		Name:         pipeshub.String("SDK Test Agent — Updated"),
		SystemPrompt: pipeshub.String("You are a helpful assistant that answers questions based on the provided knowledge base."),
		StartMessage: pipeshub.String("Hi! How can I help you today?"),
	})
	if err != nil {
		log.Fatalf("update agent: %v", err)
	}
	if updateRes == nil || updateRes.AgentUpdateResponse == nil {
		log.Fatal("update agent: empty response")
	}

	fmt.Println("\n=== Updated Agent ===")
	fmt.Printf("Status:  %s\n", updateRes.AgentUpdateResponse.Status)
	fmt.Printf("Message: %s\n", updateRes.AgentUpdateResponse.Message)

	// ─── Get updated agent ───

	getRes, err := client.Agents.GetAgent(ctx, agent.Key)
	if err != nil {
		log.Fatalf("get agent: %v", err)
	}
	if getRes == nil || getRes.GetAgentResponse == nil {
		log.Fatal("get agent: empty response")
	}

	a := getRes.GetAgentResponse.Agent
	fmt.Println("\n=== Agent After Update ===")
	fmt.Printf("Name:         %s\n", a.Name)
	fmt.Printf("Key:          %s\n", a.Key)
	if a.SystemPrompt != nil {
		fmt.Printf("SystemPrompt: %s\n", *a.SystemPrompt)
	}
	if a.StartMessage != nil {
		fmt.Printf("StartMessage: %s\n", *a.StartMessage)
	}

	// ─── Delete agent ───

	delRes, err := client.Agents.DeleteAgent(ctx, agent.Key)
	if err != nil {
		log.Fatalf("delete agent: %v", err)
	}
	if delRes == nil || delRes.AgentDeleteResponse == nil {
		log.Fatal("delete agent: empty response")
	}

	d := delRes.AgentDeleteResponse
	fmt.Println("\n=== Deleted Agent ===")
	fmt.Printf("Status:  %s\n", d.Status)
	fmt.Printf("Message: %s\n", d.Message)
	fmt.Printf("Deleted: agents=%d, toolsets=%d, tools=%d, knowledge=%d, edges=%d\n",
		d.Deleted.Agents, d.Deleted.Toolsets, d.Deleted.Tools, d.Deleted.Knowledge, d.Deleted.Edges)

	// ─── List all agents ───

	listRes, err := client.Agents.ListAgents(ctx, operations.ListAgentsRequest{})
	if err != nil {
		log.Fatalf("list agents: %v", err)
	}
	if listRes == nil || listRes.AgentListResponse == nil {
		log.Fatal("list agents: empty response")
	}

	fmt.Println("\n=== All Agents ===")
	for i, a := range listRes.AgentListResponse.Agents {
		desc, _ := a.Description.GetOrZero()
		fmt.Printf("\n%d. %s\n", i+1, a.Name)
		fmt.Printf("   Key:      %s\n", a.Key)
		fmt.Printf("   Active:   %v\n", a.IsActive)
		if desc != "" {
			fmt.Printf("   Desc:     %s\n", desc)
		}
	}
}

func findFirstConnector(ctx context.Context, sdk *pipeshub.SDK) (string, string, error) {
	res, err := sdk.KnowledgeHub.GetKnowledgeHubRootNodes(ctx, operations.GetKnowledgeHubRootNodesRequest{})
	if err != nil {
		return "", "", fmt.Errorf("get knowledge hub root nodes: %w", err)
	}
	if res == nil || res.KnowledgeHubNodesResponse == nil {
		return "", "", fmt.Errorf("get knowledge hub root nodes: empty response")
	}

	for _, n := range res.KnowledgeHubNodesResponse.GetItems() {
		if n.Origin == components.KnowledgeHubNodeOriginConnector {
			return n.ID, n.Name, nil
		}
	}

	return "", "", fmt.Errorf("no connectors found")
}

func findFirstKnowledgeBase(ctx context.Context, sdk *pipeshub.SDK) (string, string, error) {
	orgRes, err := sdk.Organizations.GetCurrentOrganization(ctx)
	if err != nil {
		return "", "", fmt.Errorf("get current organization: %w", err)
	}
	if orgRes == nil || orgRes.Organization == nil || orgRes.Organization.ID == "" {
		return "", "", fmt.Errorf("get current organization: missing organization id")
	}
	parentID := "knowledgeBase_" + orgRes.Organization.ID

	kbsRes, err := sdk.KnowledgeHub.GetKnowledgeHubChildNodes(ctx, operations.GetKnowledgeHubChildNodesRequest{
		ParentType: operations.ParentTypeApp,
		ParentID:   parentID,
	})
	if err != nil {
		return "", "", fmt.Errorf("list knowledge bases: %w", err)
	}
	if kbsRes == nil || kbsRes.KnowledgeHubNodesResponse == nil {
		return "", "", fmt.Errorf("list knowledge bases: empty response")
	}

	items := kbsRes.KnowledgeHubNodesResponse.GetItems()
	if len(items) > 0 {
		return items[0].ID, items[0].Name, nil
	}

	return "", "", fmt.Errorf("no knowledge bases found")
}