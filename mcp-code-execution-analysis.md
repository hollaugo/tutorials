# Deep Dive: Code Execution with MCP

**Source**: [Anthropic Engineering Blog - Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
**Published**: November 4, 2025
**Author**: Anthropic Engineering Team

## Executive Summary

This article introduces a paradigm shift in how AI agents interact with external tools through the Model Context Protocol (MCP). Instead of making direct tool calls, agents write code that executes in a sandboxed environment, achieving up to **98.7% reduction in token consumption** while enabling more sophisticated tool composition patterns.

---

## Part 1: The Fundamental Problem

### Problem 1: Tool Definition Overload (The "Scaling Wall")

**What happens**: As AI agents scale to support more integrations, they must load tool definitions into context before processing user requests.

**The Math**:
- An agent with access to 1,000 tools
- Each tool definition: ~100-200 tokens (function name, parameters, descriptions)
- Total overhead: **100,000-200,000 tokens** just for tool definitions
- This happens BEFORE the agent even sees the user's request

**Real-world impact**:
- Wasted context window space (could be used for actual data/instructions)
- Higher costs (you pay for these tokens on every request)
- Slower processing (more tokens to process)
- Context overflow (tools can crowd out actual work)

**Example Scenario**:
```
User: "Send my Q4 report from Google Drive to John via Slack"

Traditional approach context breakdown:
- Tool definitions: 150,000 tokens (1,500 tools × 100 tokens each)
- User message: 50 tokens
- Agent reasoning: ~1,000 tokens
- Actual useful work: Only 1,050 tokens out of 151,050!
```

### Problem 2: Intermediate Result Duplication (The "Pass-Through Problem")

**What happens**: When data flows between tools, it passes through the model context multiple times.

**Example Workflow**:
1. Agent calls `google_drive.getDocument("Q4_Report.pdf")` → Returns 50KB PDF (≈25,000 tokens)
2. Model receives entire PDF in context
3. Model decides to send it to Salesforce
4. Agent calls `salesforce.attachDocument(content=<entire_pdf>)` → PDF passes through context again
5. **Total token cost**: 50,000+ tokens just to move a file from A to B

**The Inefficiency**:
- The model doesn't need to "read" the entire document
- It just needs to orchestrate the transfer
- But with traditional tool calling, ALL data flows through the model

**More Complex Example**:
```
Task: "Find all customers in our CRM who haven't been contacted in 90 days,
       then send them a personalized email template"

Traditional tool calling:
1. crm.getAllCustomers() → Returns 10,000 customer records (500,000 tokens)
2. Model processes all 10,000 records
3. Model filters for last_contact > 90 days
4. email.sendBulk(filtered_list) → Sends list back through context
Total: ~1,000,000 tokens for a simple filtering operation
```

---

## Part 2: The Solution - Code-Based Tool Interaction

### Core Concept: Agents Write Code, Not Tool Calls

Instead of:
```json
// Traditional approach
{
  "tool": "google_drive.getDocument",
  "parameters": {"id": "doc123"}
}
// Model receives entire document in response
```

The new approach:
```typescript
// Agent writes this code
import { getDocument } from '/servers/google-drive/getDocument.ts';
import { updateRecord } from '/servers/salesforce/updateRecord.ts';

// Code executes in sandbox - data never touches model context
const doc = await getDocument("doc123");
await updateRecord({ attachment: doc });

// Only result summary returns to model
return "Successfully transferred document";
```

### The Three Key Innovations

#### 1. Progressive Disclosure (Filesystem-Based Tool Organization)

**Concept**: Tools are organized as files in a directory structure, not loaded upfront.

**Structure**:
```
/servers/
├── google-drive/
│   ├── getDocument.ts
│   ├── listFiles.ts
│   ├── createDocument.ts
│   └── shareDocument.ts
├── salesforce/
│   ├── getAccount.ts
│   ├── updateRecord.ts
│   └── createLead.ts
├── slack/
│   ├── sendMessage.ts
│   ├── listChannels.ts
│   └── uploadFile.ts
└── github/
    ├── createIssue.ts
    ├── listPRs.ts
    └── mergeRequest.ts
```

**How it works**:
1. Agent starts with no tools loaded
2. Agent explores filesystem: `ls /servers/` → sees available services
3. Agent drills down: `ls /servers/google-drive/` → sees Google Drive tools
4. Agent reads only needed tools: `cat /servers/google-drive/getDocument.ts`
5. Only loads the 2-3 tools actually needed (200-300 tokens instead of 200,000)

**Benefits**:
- **Lazy loading**: Load tools only when needed
- **Discoverability**: Agents can explore what's available
- **Scalability**: Can support 10,000+ tools without context bloat
- **Organization**: Natural hierarchical grouping

#### 2. On-Demand Discovery

**Traditional Approach** (Front-loaded):
```
System: Here are ALL 1,500 tools you can use... [150,000 tokens]
User: Send a Slack message
Agent: *searches through 1,500 tool definitions* Found it!
```

**Code Execution Approach** (Lazy):
```
User: Send a Slack message
Agent: Let me check what's available...
  → ls /servers/ → sees "slack/"
  → ls /servers/slack/ → sees "sendMessage.ts"
  → cat /servers/slack/sendMessage.ts → reads ONLY this tool
  → writes code to call it
[Used maybe 500 tokens total for discovery]
```

**Key Insight**: Most tasks only need 2-5 tools, so why load 1,500?

#### 3. Local Data Processing

**The Game-Changer**: Process data in the execution environment, not in model context.

**Example 1: Large Dataset Filtering**
```typescript
// This runs in sandbox, NOT in model context
import { getAllCustomers } from '/servers/crm/getAllCustomers.ts';

const customers = await getAllCustomers(); // 10,000 records
// Filter locally - data never goes to model
const inactive = customers.filter(c =>
  daysSince(c.lastContact) > 90
);

// Return only summary to model
return {
  count: inactive.length,
  sampleCustomers: inactive.slice(0, 3) // Just 3 examples
};
```

**Token Comparison**:
- Traditional: 500,000 tokens (all customers passed through model)
- Code execution: 500 tokens (just the summary)
- **Savings**: 99.9%

**Example 2: Multi-Step Data Pipeline**
```typescript
// Agent writes this - executes in sandbox
import { getDocument } from '/servers/google-drive/getDocument.ts';
import { analyzeText } from '/servers/analysis/analyzeText.ts';
import { updateRecord } from '/servers/salesforce/updateRecord.ts';

// Step 1: Fetch large document (50KB)
const doc = await getDocument("report.pdf");

// Step 2: Extract just the key metrics locally
const summary = analyzeText(doc, { extractMetrics: true });

// Step 3: Store summary in Salesforce
await updateRecord({
  id: "lead_123",
  summary: summary.keyMetrics // Only 200 bytes
});

return "Updated lead with Q4 metrics";
```

**Flow**:
1. 50KB document retrieved → stays in sandbox
2. Analyzed locally → intermediate results stay in sandbox
3. Only 200-byte summary sent to Salesforce
4. Model only sees final status message

**Tokens through model**: ~50 (status message)
**Traditional approach**: ~75,000 tokens (document + analysis + summary all through model)

---

## Part 3: Beyond Token Savings - Additional Benefits

### Benefit 1: Privacy Protection

**Problem**: In traditional tool calling, ALL data flows through the model, including sensitive information.

**Code Execution Solution**:

```typescript
// Data processing happens in sandbox
import { getCustomers } from '/servers/crm/getCustomers.ts';
import { sendEmail } from '/servers/email/sendEmail.ts';

const customers = await getCustomers(); // Contains PII

// The MCP client can tokenize PII before sending to model
customers.forEach(customer => {
  const template = `Hello ${tokenize(customer.name)}, ...`;
  sendEmail(customer.email, template);
});

return "Sent 100 personalized emails"; // No PII to model
```

**Tokenization Concept**:
- Sensitive data replaced with tokens like `<USER_NAME_1>`, `<EMAIL_1>`
- Actual data stays in execution environment
- Model can still orchestrate workflow
- Data flows between services without touching model

**Use Cases**:
- Healthcare: HIPAA-compliant agent workflows
- Finance: Handle sensitive financial data
- HR: Process employee records privately
- Legal: Work with confidential documents

### Benefit 2: Stateful Agents & Persistent Skills

**Concept**: Agents can write files to persist state and build reusable capabilities.

**Example: Building a Skill Library**
```typescript
// Agent discovers a useful pattern and saves it
import { writeFile } from 'fs/promises';

async function fetchAndSummarizeReport(reportId: string) {
  const doc = await getDocument(reportId);
  const summary = analyzeText(doc, { maxLength: 200 });
  return summary;
}

// Save for future use
await writeFile(
  '/skills/fetchAndSummarizeReport.ts',
  fetchAndSummarizeReport.toString()
);
```

**Later**:
```typescript
// Agent can reuse the skill
import { fetchAndSummarizeReport } from '/skills/fetchAndSummarizeReport.ts';

const q3Report = await fetchAndSummarizeReport("q3_2025");
const q4Report = await fetchAndSummarizeReport("q4_2025");

return `Q3: ${q3Report}\nQ4: ${q4Report}`;
```

**Benefits**:
- **Learning**: Agents build up capability libraries
- **Efficiency**: Reuse proven patterns
- **Long-running tasks**: Checkpoint progress, resume after interruption
- **Complex workflows**: Break down into reusable components

**Long-Running Task Example**:
```typescript
// Checkpoint progress for a multi-day task
import { writeFile, readFile } from 'fs/promises';

let progress = { processed: 0, total: 10000, lastId: null };

// Try to resume from checkpoint
try {
  progress = JSON.parse(await readFile('/state/progress.json', 'utf-8'));
} catch {}

const customers = await getCustomers({ afterId: progress.lastId });

for (const customer of customers) {
  await processCustomer(customer);
  progress.processed++;
  progress.lastId = customer.id;

  // Checkpoint every 100 customers
  if (progress.processed % 100 === 0) {
    await writeFile('/state/progress.json', JSON.stringify(progress));
  }
}
```

### Benefit 3: Efficient Control Flow

**Problem**: With traditional tool calling, loops and conditionals require model round-trips.

**Traditional Approach** (5 round-trips for a loop):
```
User: "Send welcome emails to all new customers"

Round 1:
Agent: [calls getNewCustomers()]
Result: [customer1, customer2, customer3, customer4, customer5]

Round 2:
Agent: [calls sendEmail(customer1.email)]
Result: "Sent"

Round 3:
Agent: [calls sendEmail(customer2.email)]
Result: "Sent"

Round 4:
Agent: [calls sendEmail(customer3.email)]
Result: "Sent"

[... continues for all customers]
```

**Code Execution Approach** (1 execution):
```typescript
const customers = await getNewCustomers();

for (const customer of customers) {
  try {
    await sendEmail(customer.email, welcomeTemplate);
  } catch (error) {
    // Handle errors locally
    console.error(`Failed for ${customer.id}: ${error}`);
  }
}

return `Sent ${customers.length} welcome emails`;
```

**Performance Improvement**:
- **Latency**: 1 execution vs. N model round-trips
- **Reliability**: Error handling in code vs. model context
- **Cost**: Pay for one code execution vs. N tool calls through model
- **Complexity**: Standard programming constructs vs. prompt engineering

**Advanced Control Flow Example**:
```typescript
// Retry logic with exponential backoff
async function robustAPICall(fn: Function, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(Math.pow(2, i) * 1000); // Exponential backoff
    }
  }
}

// Use it
const data = await robustAPICall(() => getUnreliableData());
```

**This would be extremely inefficient as tool calls** - each retry would require a full model round-trip!

---

## Part 4: Implementation Considerations & Trade-offs

### Requirements for Code Execution

#### 1. Secure Sandboxing

**Why it's critical**: Agents are writing arbitrary code that executes in your infrastructure.

**Security measures needed**:
- **Isolated execution environment** (containers, VMs, or WebAssembly)
- **Resource limits**: CPU, memory, disk, network
- **Filesystem restrictions**: Read/write permissions
- **Network policies**: Whitelist allowed endpoints
- **Timeout enforcement**: Kill runaway processes
- **Code inspection**: Static analysis for dangerous patterns

**Example Sandbox Configuration**:
```json
{
  "runtime": "isolated_container",
  "limits": {
    "cpu": "1 core",
    "memory": "512MB",
    "disk": "1GB",
    "timeout": "30s",
    "network_bandwidth": "10MB/s"
  },
  "permissions": {
    "filesystem": {
      "/servers/": "read",
      "/skills/": "read+write",
      "/tmp/": "read+write"
    },
    "network": {
      "allowed_domains": ["*.internal.company.com"],
      "blocked_domains": ["*"]
    }
  }
}
```

#### 2. Monitoring & Observability

**What to monitor**:
- Code execution time
- Resource consumption (CPU, memory, I/O)
- API calls made from sandbox
- Error rates and types
- Security violations

**Example Monitoring**:
```typescript
// Instrumentation wrapper
function instrumentedExecute(code: string) {
  const startTime = Date.now();
  const metrics = {
    apiCalls: [],
    resourceUsage: {},
    errors: []
  };

  try {
    const result = sandbox.execute(code, {
      onAPICall: (call) => metrics.apiCalls.push(call),
      onError: (error) => metrics.errors.push(error)
    });

    metrics.resourceUsage = sandbox.getResourceUsage();
    metrics.duration = Date.now() - startTime;

    logMetrics(metrics);
    return result;
  } catch (error) {
    alertOnFailure(error, metrics);
    throw error;
  }
}
```

#### 3. Cost-Benefit Analysis

**Operational Costs** (Code Execution):
- Infrastructure for sandboxing
- Monitoring systems
- Security auditing
- Development complexity

**Savings** (Token Reduction):
- Up to 98.7% fewer tokens
- At $3/million input tokens (Claude Opus):
  - Traditional: $3 per 1M tokens
  - Code execution: $0.039 per 1M tokens (98.7% reduction)
- For 1 billion tokens/month: Save $2,961/month

**Break-even Analysis**:
```
Monthly costs:
- Sandbox infrastructure: $500/month (AWS Fargate)
- Monitoring: $100/month
- Development: $200/month (amortized)
Total: $800/month

Token savings: $2,961/month

Net benefit: $2,161/month (270% ROI)
```

**When it makes sense**:
- High tool usage (>1000 tools available)
- Large data processing workflows
- Privacy-sensitive applications
- Complex multi-step automations

**When traditional tool calling is better**:
- Simple agents (5-10 tools)
- Minimal data processing
- Security-critical environments where sandboxing is too risky
- Low request volume (setup costs not amortized)

---

## Part 5: Real-World Validation & Adoption

### Cloudflare's "Code Mode"

**What they found**:
- Independently developed same pattern
- Called it "Code Mode"
- Published similar findings about efficiency gains
- Validates that LLMs are better at writing code than making tool calls

**Cloudflare's insight**:
> "Large language models are fundamentally better at generating code that orchestrates APIs than they are at directly calling APIs through tool definitions."

**Why LLMs prefer code**:
1. **Training data**: Most of training data is code, not tool call JSON
2. **Natural expression**: Code is how humans express logic
3. **Familiar patterns**: Loops, conditionals, error handling are native to code
4. **Composability**: Code naturally supports complex compositions

### Industry Trend

**Signal**: Multiple major AI companies converging on same solution independently indicates:
- Fundamental efficiency advantage
- Natural fit with LLM capabilities
- Future direction of agent architectures

---

## Part 6: Architectural Patterns & Best Practices

### Pattern 1: The Exploration Phase

**Agent workflow**:
```typescript
// Phase 1: Discover available services
const services = await listDirectory('/servers/');
console.log('Available:', services);
// → ['google-drive', 'salesforce', 'slack', 'github']

// Phase 2: Narrow down to relevant service
const driveTools = await listDirectory('/servers/google-drive/');
console.log('Google Drive tools:', driveTools);
// → ['getDocument.ts', 'listFiles.ts', 'createDocument.ts']

// Phase 3: Load only needed tool definition
const toolDef = await readFile('/servers/google-drive/getDocument.ts');
// Now agent understands this specific tool

// Phase 4: Use it
import { getDocument } from '/servers/google-drive/getDocument.ts';
const doc = await getDocument('doc_id');
```

**Best practice**: Design tool filesystem hierarchy to match user mental models.

### Pattern 2: The Data Pipeline

**For multi-step data transformations**:
```typescript
// Import all needed tools upfront
import { getDocument } from '/servers/google-drive/getDocument.ts';
import { extractText } from '/servers/ocr/extractText.ts';
import { translateText } from '/servers/translation/translateText.ts';
import { sendEmail } from '/servers/email/sendEmail.ts';

// Pipeline: retrieve → process → transform → deliver
const pdf = await getDocument('quarterly_report.pdf');
const text = await extractText(pdf);
const translated = await translateText(text, { to: 'es' });
await sendEmail({
  to: 'team@company.com',
  subject: 'Q4 Report (Spanish)',
  body: translated
});

// Model only sees final result
return 'Successfully sent translated report';
```

**Key insight**: Intermediate results (50KB PDF, extracted text, translation) never touch model context.

### Pattern 3: The Aggregation Pattern

**For collecting and summarizing data from multiple sources**:
```typescript
import { getGithubPRs } from '/servers/github/listPRs.ts';
import { getJiraIssues } from '/servers/jira/getIssues.ts';
import { getSlackMessages } from '/servers/slack/getMessages.ts';

// Collect from multiple sources
const prs = await getGithubPRs({ state: 'open' });
const issues = await getJiraIssues({ assignee: 'me' });
const messages = await getSlackMessages({ channel: 'engineering', unread: true });

// Aggregate locally
const summary = {
  openPRs: prs.length,
  urgentIssues: issues.filter(i => i.priority === 'high').length,
  unreadMessages: messages.length,
  actionItems: [
    ...prs.slice(0, 3).map(pr => `Review PR: ${pr.title}`),
    ...issues.slice(0, 3).map(i => `Resolve: ${i.title}`)
  ]
};

return summary; // Compact summary vs. thousands of items
```

### Pattern 4: The Skill Library Pattern

**Building reusable abstractions**:
```typescript
// /skills/notification.ts
export async function notifyTeam(message: string, urgent: boolean = false) {
  const channels = urgent
    ? ['#engineering', '#leadership']
    : ['#engineering'];

  for (const channel of channels) {
    await sendSlackMessage({ channel, message });
  }

  if (urgent) {
    await sendEmail({
      to: 'oncall@company.com',
      subject: 'URGENT: ' + message,
      body: message
    });
  }
}

// Now agents can use high-level abstractions
import { notifyTeam } from '/skills/notification.ts';
await notifyTeam('Deployment failed', true);
```

---

## Part 7: Comparison Matrix

| Aspect | Traditional Tool Calling | Code Execution |
|--------|-------------------------|----------------|
| **Context Usage** | High (all tool defs loaded) | Low (lazy loading) |
| **Token Efficiency** | Baseline | Up to 98.7% reduction |
| **Scalability** | Poor (1000+ tools = context overflow) | Excellent (unlimited tools) |
| **Data Privacy** | All data through model | Data stays in sandbox |
| **Control Flow** | Inefficient (model round-trips) | Efficient (native code) |
| **State Management** | Stateless (each call independent) | Stateful (persistent storage) |
| **Error Handling** | Limited (model-based) | Rich (try/catch, retries) |
| **Setup Complexity** | Low | High (sandboxing required) |
| **Security Concerns** | Lower | Higher (arbitrary code execution) |
| **Best For** | Simple agents, few tools | Complex agents, many tools |

---

## Part 8: Future Implications

### Architectural Shift

This represents a fundamental change in agent architecture:

**Old paradigm**:
```
User → LLM → Tool Call → Service → Result → LLM → Response
         ↑_________________↑ (data flows through LLM)
```

**New paradigm**:
```
User → LLM → Code → Sandbox → Services → Result → LLM → Response
                      ↑___________________↑ (data flows through sandbox)
```

### Potential Evolution

**Near future**:
- Standardized sandbox specifications
- Tool definition formats optimized for filesystem organization
- Built-in skill libraries across platforms

**Long-term possibilities**:
- Agents that self-improve by writing better utilities
- Collaborative agent systems sharing skill libraries
- Domain-specific agent "operating systems"

### Questions for the Community

1. **Security**: What's the right balance between capability and safety?
2. **Standards**: Should there be a standard filesystem structure for MCP tools?
3. **Sharing**: How can agents safely share learned skills?
4. **Observability**: What metrics matter most for code-executing agents?

---

## Key Takeaways

1. **Token efficiency**: Code execution can reduce token usage by 98.7% for tool-heavy agents
2. **Scalability**: Enables agents to scale to thousands of tools without context overflow
3. **Privacy**: Keeps sensitive data out of model context while allowing workflow orchestration
4. **Complexity**: Requires significant infrastructure (sandboxing, monitoring, security)
5. **Validation**: Multiple companies converging on this pattern independently
6. **Future**: Likely to become standard for complex agent systems

## When to Use This Approach

**✅ Good fit**:
- Agents with 100+ available tools
- Workflows involving large data processing
- Privacy-sensitive applications
- Complex multi-step automations
- High request volumes (to amortize setup costs)

**❌ Not necessary**:
- Simple agents with 5-10 tools
- Minimal data processing
- Low security tolerance for sandboxing
- Prototype/early-stage development

---

## Further Reading

- [Model Context Protocol Specification](https://modelcontextprotocol.io)
- [Cloudflare's Code Mode Blog Post](https://blog.cloudflare.com/workers-ai-code-mode)
- [Anthropic MCP Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-06
**Analysis By**: Claude (Sonnet 4.5)
