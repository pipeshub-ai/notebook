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

	// ─── List all agents ───

	listRes, err := client.Agents.ListAgents(ctx, operations.ListAgentsRequest{})
	if err != nil {
		log.Fatalf("list agents: %v", err)
	}
	if listRes == nil || listRes.AgentListResponse == nil {
		log.Fatal("list agents: empty response")
	}

	fmt.Println("=== All Agents ===")
	for i, a := range listRes.AgentListResponse.Agents {
		desc, _ := a.Description.GetOrZero()
		fmt.Printf("\n%d. %s\n", i+1, a.Name)
		fmt.Printf("   Key:      %s\n", a.Key)
		fmt.Printf("   Active:   %v\n", a.IsActive)
		if desc != "" {
			fmt.Printf("   Desc:     %s\n", desc)
		}
	}

	// ─── Get one agent (using key of first listed) ───

	agents := listRes.AgentListResponse.Agents
	if len(agents) == 0 {
		log.Fatal("no agents found")
	}
	firstKey := agents[0].Key

	getRes, err := client.Agents.GetAgent(ctx, firstKey)
	if err != nil {
		log.Fatalf("get agent: %v", err)
	}
	if getRes == nil || getRes.GetAgentResponse == nil {
		log.Fatal("get agent: empty response")
	}

	a := getRes.GetAgentResponse.Agent

	fmt.Println("\n=== Agent Detail ===")
	fmt.Printf("Name:       %s\n", a.Name)
	fmt.Printf("Key:        %s\n", a.Key)
	fmt.Printf("ID:         %s\n", a.ID)
	fmt.Printf("Active:     %v\n", a.IsActive)
	fmt.Printf("ShareOrg:   %v\n", a.ShareWithOrg)

	inst, _ := a.Instructions.GetOrZero()
	if inst != "" {
		fmt.Printf("Instructions: %s\n", inst)
	}
	if a.SystemPrompt != nil {
		fmt.Printf("SystemPrompt:  %s\n", *a.SystemPrompt)
	}
	if a.StartMessage != nil {
		fmt.Printf("StartMessage:  %s\n", *a.StartMessage)
	}

	fmt.Printf("Tags:           %v\n", a.Tags)
	if a.ModelConfig != nil {
		fmt.Printf("ModelConfig:    key=%s\n", *a.ModelConfig.ModelKey)
	}
	fmt.Printf("Tools:          %v\n", a.Tools)
	fmt.Printf("KnowledgeBases: %v\n", a.KnowledgeBases)
}
