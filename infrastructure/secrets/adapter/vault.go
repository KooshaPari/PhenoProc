package adapter

import (
	"context"
	"github.com/koosha/pari/infrastructure/pkg/errors"
	"os/exec"
	"strings"

	"github.com/KooshaPari/phenotype-go-kit/contracts/ports/outbound"
)

// VaultAdapter implements outbound.SecretPort for HashiCorp Vault.
type VaultAdapter struct {
	mountPath string
}

// NewVaultAdapter creates a new Vault adapter.
func NewVaultAdapter(mountPath string) *VaultAdapter {
	return &VaultAdapter{
		mountPath: mountPath,
	}
}

// Get implements outbound.SecretPort.
func (a *VaultAdapter) Get(ctx context.Context, key string) (*outbound.SecretValue, error) {
	cmd := exec.CommandContext(ctx, "vault", "kv", "get",
		"-format=json",
		"secret/data/"+key,
	)
	output, err := cmd.Output()
	if err != nil {
		return nil, errors.Wrap(err, "vault get failed")
	}

	// Parse JSON output (simplified - use proper JSON parsing in production)
	return &outbound.SecretValue{
		Key:   key,
		Value: strings.TrimSpace(string(output)),
	}, nil
}

// Set implements outbound.SecretPort.
func (a *VaultAdapter) Set(ctx context.Context, key string, value string, opts ...outbound.SecretOption) error {
	cmd := exec.CommandContext(ctx, "vault", "kv", "put",
		"secret/data/"+key,
		"value="+value,
	)
	if err := cmd.Run(); err != nil {
		return errors.Wrap(err, "vault set failed")
	}
	return nil
}

// Delete implements outbound.SecretPort.
func (a *VaultAdapter) Delete(ctx context.Context, key string) error {
	cmd := exec.CommandContext(ctx, "vault", "kv", "delete",
		"secret/data/"+key,
	)
	if err := cmd.Run(); err != nil {
		return errors.Wrap(err, "vault delete failed")
	}
	return nil
}

// List implements outbound.SecretPort.
func (a *VaultAdapter) List(ctx context.Context, path string) ([]string, error) {
	cmd := exec.CommandContext(ctx, "vault", "kv", "list",
		"secret/metadata/"+path,
	)
	output, err := cmd.Output()
	if err != nil {
		return nil, errors.Wrap(err, "vault list failed")
	}

	lines := strings.Split(strings.TrimSpace(string(output)), "\n")
	return lines[1:], nil // Skip header
}

// Exists implements outbound.SecretPort.
func (a *VaultAdapter) Exists(ctx context.Context, key string) (bool, error) {
	cmd := exec.CommandContext(ctx, "vault", "kv", "get",
		"secret/data/"+key,
	)
	err := cmd.Run()
	if err != nil {
		return false, nil
	}
	return true, nil
}
