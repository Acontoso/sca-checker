# SCA Dependency Snyk Checker

This repository contains a FastAPI service for software composition analysis workflows. It is designed to run locally for development and in AWS Lambda for deployment, with API Gateway and Cognito protecting the public API surface.

The service is primarily used by Security Copilot to support agentic and natural-language interactions. In practice, that means a Copilot workflow can ask the API whether an open source package exists in Snyk-tracked dependency inventory, or enrich a package with malicious-package intelligence, then use the response to drive follow-up reasoning, prompts, or remediation guidance.

## Purpose

The API exposes two main SCA routes:

1. `POST /sca/check`
2. `POST /sca/enrich`

Together, these routes let a caller move from package discovery to risk enrichment:

- `POST /sca/check` answers whether a package and version are present in Snyk-backed dependency search results for a target business unit or across all configured business units.
- `POST /sca/enrich` answers whether a package is known to be malicious and returns threat details when a malicious match is found.

This separation is intentional. The first route is inventory and presence oriented. The second route is threat-intelligence oriented.

## Route Capabilities

### `POST /sca/check`

Checks whether a package exists in the selected ecosystem and returns dependency discovery results from Snyk.

Request highlights:

- `language`: one of `dotnet`, `python`, `java`, `javascript`
- `package_name`: package to search for
- `version`: package version to evaluate
- `business_unit`: one of `all`

What it does:

- Maps the requested language to a package manager (`nuget`, `pip`, `maven`, `npm`)
- Resolves the target Snyk organization from the requested business unit
- Verifies package existence in Snyk
- Searches Snyk dependency data for the package and version
- Supports fan-out across all configured business units when `business_unit=all`

Typical use cases:

- Determine whether a dependency is already present in monitored projects
- Check whether a specific package version exists before triage or escalation
- Let Security Copilot ground a natural-language investigation in Snyk-backed inventory data

Example request:

```json
{
	"language": "python",
	"package_name": "requests",
	"version": "2.32.3",
	"business_unit": "all"
}
```

Example response shape:

```json
[
	{
		"exist": true,
		"package_name": "requests",
		"version": "2.32.3",
		"package_manager": "pip",
		"snyk_response": {
			"results": []
		}
	}
]
```

### `POST /sca/enrich`

Enriches a package with malicious-package intelligence from the Open Source Malware API.

Request highlights:

- `package_name`: package to search for
- `ecosystem`: one of `npm`, `pypi`, `maven`, `javascript`, `nuget`
- `version`: optional package version

What it does:

- Calls the Open Source Malware package check API
- Determines whether the package is flagged as malicious
- Returns a clean or malicious response model
- Includes threat counts and threat details when a malicious match is returned

Typical use cases:

- Enrich package findings with malicious-package context
- Support analyst or Copilot workflows for package triage
- Add threat intelligence to a natural-language SCA investigation

Example request:

```json
{
	"package_name": "example-package",
	"ecosystem": "npm",
	"version": "1.0.0"
}
```

Example response shape for a clean package:

```json
{
	"malicious": false,
	"package_name": "example-package",
	"ecosystem": "npm",
	"version": "1.0.0",
	"threat_count": null,
	"message": "No malicious indicators found"
}
```

## Security Copilot Use Case

This API is intended to be a backend capability for Security Copilot. The service is a strong fit for agentic and natural-language interaction patterns because it provides compact, structured answers to questions such as:

- Is this package and version present in our monitored Snyk footprint?
- Which business unit is it associated with?
- Is this package known to be malicious?
- If it is malicious, what threat details should be surfaced to an analyst?

That makes the API suitable for Copilot skills, plugins, or orchestration layers that convert freeform analyst questions into deterministic SCA checks.

## Authentication and Access

The two SCA routes are protected by Cognito bearer-token authentication.

- Authentication type: `Bearer`
- Required token type: Cognito access token
- Default required scope: `sca-api/ioc.lookup.all`

Configuration is read from environment variables:

- `COGNITO_ISSUER` or `COGNITO_ISSUER_URL`
- or `COGNITO_REGION` and `COGNITO_USER_POOL_ID`
- optional `COGNITO_REQUIRED_SCOPE`

## Runtime and Integrations

The service is built with FastAPI and can run in two modes:

- Local development via Uvicorn
- AWS Lambda via Mangum

Primary integrations:

- Snyk API for dependency discovery
- Open Source Malware API for malicious-package enrichment
- AWS SSM Parameter Store and KMS for secret retrieval in Lambda
- API Gateway and Cognito provisioned through Terraform

