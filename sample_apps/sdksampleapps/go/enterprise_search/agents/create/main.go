package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"github.com/joho/godotenv"
	pipeshub "github.com/pipeshub-ai/pipeshub-sdk-go"
	"github.com/pipeshub-ai/pipeshub-sdk-go/models/components"

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

	// ─── Create agent ───

	createRes, err := client.Agents.CreateAgent(ctx, components.AgentCreateRequest{
		Name: "SDK Test Agent",
		Models: []components.AgentCreateModelEntryUnion{
			components.CreateAgentCreateModelEntryUnionAgentCreateModelEntry(
				components.AgentCreateModelEntry{
					ModelKey:    "f1ffcb38-5fa4-4d77-ac70-8ca8af08be7c",
					IsReasoning: pipeshub.Bool(true),
				},
			),
		},
	})
	if err != nil {
		log.Fatalf("create agent: %v", err)
	}
	if createRes == nil || createRes.AgentCreateResponse == nil {
		log.Fatal("create agent: empty response")
	}

	agent := createRes.AgentCreateResponse.Agent
	fmt.Printf("=== Created Agent ===\n")
	fmt.Printf("Name:  %s\n", agent.Name)
	fmt.Printf("Key:   %s\n", agent.Key)

	// ─── Get agent ───

	getRes, err := client.Agents.GetAgent(ctx, agent.Key)
	if err != nil {
		log.Fatalf("get agent: %v", err)
	}
	if getRes == nil || getRes.GetAgentResponse == nil {
		log.Fatal("get agent: empty response")
	}

	a := getRes.GetAgentResponse.Agent
	fmt.Println("\n=== Agent Detail ===")
	fmt.Printf("Name:           %s\n", a.Name)
	fmt.Printf("Key:            %s\n", a.Key)
	fmt.Printf("Active:         %v\n", a.IsActive)
	if a.SystemPrompt != nil {
		fmt.Printf("SystemPrompt:   %s\n", *a.SystemPrompt)
	}
	fmt.Printf("Models:         %v\n", a.Models)
}