# Frontend Architecture - Premium AI-Native UI

## Vision

A **premium, fast, AI-native** interface that feels like a professional IDE meets a command center. The AI assistant is not a chatbot—it's a contextual copilot integrated into every view.

## Design Principles

1. **AI-First UX**: Command surface (palette + dock) acts on current context
2. **Clarity over Chrome**: Crisp hierarchy, generous white space, restrained color
3. **Instant Legibility**: Dense data layouts that remain scannable (4/8pt grid)
4. **Motion with Purpose**: Subtle micro-interactions (120-200ms) to guide attention
5. **Accessible by Default**: WCAG 2.2 AA, keyboard-first, focus rings, high-contrast

## Information Architecture

### Global Layout

```
┌──────────────────────────────────────────────────────────┐
│  Top Navbar: Brand | Nav | Search/Command | User         │
├────────┬─────────────────────────────────────┬───────────┤
│  Left  │      Main Content Area              │   Right   │
│  Rail  │                                     │  AI Dock  │
│  (Nav) │      Dynamic per Route              │ (Context) │
│        │                                     │           │
│ 240px  │           Flex                      │   360px   │
└────────┴─────────────────────────────────────┴───────────┘
```

### Route Structure

```
/
├── /                          # Home (Overview, Notifications)
├── /projects                  # Project List
│   ├── /:id                   # Project Detail (Board, Specs, PRs)
│   └── /:id/settings          # Project Settings
├── /agents                    # Agent Roster
│   ├── /:agentId              # Agent Detail (Skills, Playbooks)
│   └── /compose               # Crew Composer Wizard
├── /analytics                 # Metrics Dashboard
│   ├── /costs                 # Cost Analytics
│   ├── /performance           # Performance Metrics
│   └── /quality               # Quality Trends
├── /integrations              # External Integrations
│   └── /:integrationId        # Integration Detail
└── /settings                  # Org Settings
    ├── /account               # User Account
    ├── /team                  # Team Management
    └── /appearance            # Theme, Preferences
```

## Design System

### Typography

```typescript
const typography = {
  display: {
    family: 'General Sans',
    weight: 800,
    sizes: {
      xl: '3.5rem',    // 56px
      lg: '2.5rem',    // 40px
      md: '2rem',      // 32px
    }
  },
  heading: {
    family: 'Inter',
    weight: 700,
    sizes: {
      h1: '1.875rem',  // 30px
      h2: '1.5rem',    // 24px
      h3: '1.25rem',   // 20px
      h4: '1.125rem',  // 18px
    }
  },
  body: {
    family: 'Inter',
    weight: { regular: 400, medium: 500, semibold: 600 },
    sizes: {
      lg: '1.125rem',  // 18px
      md: '1rem',      // 16px
      sm: '0.875rem',  // 14px
      xs: '0.75rem',   // 12px
    }
  },
  mono: {
    family: 'JetBrains Mono',
    sizes: {
      md: '0.875rem',  // 14px
      sm: '0.75rem',   // 12px
    }
  }
}
```

### Spacing & Layout

```typescript
const spacing = {
  // 4pt base grid
  base: 4,
  scale: {
    0: '0',
    1: '0.25rem',  // 4px
    2: '0.5rem',   // 8px
    3: '0.75rem',  // 12px
    4: '1rem',     // 16px
    5: '1.25rem',  // 20px
    6: '1.5rem',   // 24px
    8: '2rem',     // 32px
    10: '2.5rem',  // 40px
    12: '3rem',    // 48px
    16: '4rem',    // 64px
  }
}

const borderRadius = {
  sm: '0.375rem',   // 6px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  full: '9999px'
}
```

### Color System

#### Light Theme
```typescript
const lightTheme = {
  brand: {
    primary: '#4F46E5',    // Indigo-600
    hover: '#4338CA',      // Indigo-700
    active: '#3730A3',     // Indigo-800
  },
  ink: {
    primary: '#0B1020',    // Near black
    secondary: '#374151',  // Gray-700
    tertiary: '#6B7280',   // Gray-500
    disabled: '#9CA3AF',   // Gray-400
  },
  surface: {
    primary: '#FFFFFF',
    secondary: '#F9FAFB',  // Gray-50
    tertiary: '#F3F4F6',   // Gray-100
    overlay: '#00000014',  // Black 8%
  },
  border: {
    subtle: '#E5E7EB',     // Gray-200
    default: '#D1D5DB',    // Gray-300
    strong: '#9CA3AF',     // Gray-400
  },
  status: {
    success: '#10B981',    // Green-500
    warning: '#F59E0B',    // Amber-500
    danger: '#EF4444',     // Red-500
    info: '#06B6D4',       // Cyan-500
  }
}
```

#### Dark Theme
```typescript
const darkTheme = {
  brand: {
    primary: '#A5B4FC',    // Indigo-300
    hover: '#C7D2FE',      // Indigo-200
    active: '#E0E7FF',     // Indigo-100
  },
  ink: {
    primary: '#E6EAF5',    // Near white
    secondary: '#D1D5DB',  // Gray-300
    tertiary: '#9CA3AF',   // Gray-400
    disabled: '#6B7280',   // Gray-500
  },
  surface: {
    primary: '#0B1220',    // Near black
    secondary: '#111827',  // Gray-900
    tertiary: '#1F2937',   // Gray-800
    overlay: '#FFFFFF14',  // White 8%
  },
  border: {
    subtle: '#1F2937',     // Gray-800
    default: '#374151',    // Gray-700
    strong: '#4B5563',     // Gray-600
  },
  status: {
    success: '#34D399',    // Green-400
    warning: '#FBBF24',    // Amber-400
    danger: '#F87171',     // Red-400
    info: '#22D3EE',       // Cyan-400
  }
}
```

### Elevation (Shadows)

```typescript
const shadows = {
  e0: 'none',
  e1: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  e2: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  e3: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  e4: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
}
```

## Core Components

### App Shell Components

#### 1. Top Navbar
```tsx
<TopNav>
  <Left>
    <Brand /> {/* Logo + Product Switcher */}
    <NavLinks /> {/* Projects, Agents, Analytics */}
  </Left>
  <Center>
    <CommandTrigger /> {/* ⌘K to open palette */}
  </Center>
  <Right>
    <RunsIndicator /> {/* Active workflow count */}
    <NotificationBell />
    <UserMenu />
  </Right>
</TopNav>
```

**Key Behaviors**:
- Sticky on scroll
- Backdrop blur when scrolling (frosted glass)
- Active route highlighted
- Keyboard shortcut hints on hover

#### 2. Left Rail (Context Navigation)
```tsx
<LeftRail>
  <NavSection title="Workspace">
    <NavItem icon={<HomeIcon />} label="Home" href="/" />
    <NavItem icon={<ProjectIcon />} label="Projects" href="/projects" />
    <NavItem icon={<AgentIcon />} label="Agents" href="/agents" />
  </NavSection>
  <NavSection title="Insights">
    <NavItem icon={<ChartIcon />} label="Analytics" href="/analytics" />
    <NavItem icon={<PlugIcon />} label="Integrations" href="/integrations" />
  </NavSection>
  <NavSection title="Settings">
    <NavItem icon={<SettingsIcon />} label="Settings" href="/settings" />
  </NavSection>
</LeftRail>
```

**Key Behaviors**:
- Collapsible to icon-only (48px → 240px)
- Tooltips on hover when collapsed
- Active state with accent indicator
- Keyboard navigation (Tab, Arrow keys)

#### 3. AI Dock (Contextual Copilot)
```tsx
<AIDock>
  <DockHeader>
    <Title>Project: {projectName}</Title>
    <Actions>
      <CollapseButton />
      <SettingsButton />
    </Actions>
  </DockHeader>

  <DockTabs>
    <Tab>Exec Summary</Tab>
    <Tab>Risks</Tab>
    <Tab>Actions</Tab>
  </DockTabs>

  <DockContent>
    {/* Context-aware based on current route */}
    <ExecSummary />
    <RiskList />
    <SuggestedActions>
      <ActionChip onClick={handleAction}>
        ✦ Summarize PR #104
      </ActionChip>
      <ActionChip>
        ✦ Generate test plan
      </ActionChip>
      <ActionChip>
        ✦ Estimate costs
      </ActionChip>
    </SuggestedActions>
  </DockContent>

  <DockFooter>
    <PromptBar placeholder="Ask AI..." />
  </DockFooter>
</AIDock>
```

**Context Awareness**:
- On `/projects/:id` → Suggests: "Summarize recent PRs", "Create roadmap"
- On PR detail → Suggests: "Review changes", "Generate tests", "Estimate risk"
- On `/agents` → Suggests: "Compose crew for migration", "Benchmark models"

### Signature Interactions

#### 1. Universal Command Palette (⌘K)

```tsx
<CommandPalette>
  <SearchInput
    placeholder="Search or run command..."
    icon={<SearchIcon />}
  />

  <ResultGroups>
    <Group title="Actions">
      <Result icon={<SpecIcon />} shortcut="⌘ N">
        /spec new - Create new specification
      </Result>
      <Result icon={<ReviewIcon />} shortcut="⌘ R">
        /review - Start code review
      </Result>
    </Group>

    <Group title="Navigate">
      <Result icon={<ProjectIcon />}>
        Projects › Orion
      </Result>
      <Result icon={<IssueIcon />}>
        #54 - Implement auth flow
      </Result>
    </Group>

    <Group title="AI Recipes">
      <Result icon={<AIIcon />}>
        Generate migration plan
      </Result>
    </Group>
  </ResultGroups>

  <Footer>
    <Shortcuts>
      <Shortcut>↑↓ Navigate</Shortcut>
      <Shortcut>↵ Select</Shortcut>
      <Shortcut>⇧↵ Run in Dock</Shortcut>
    </Shortcuts>
  </Footer>
</CommandPalette>
```

**Features**:
- Fuzzy search across entities
- Slash commands (`/spec`, `/review`, `/deploy`)
- Recent items prioritized
- AI action suggestions
- Preview pane (optional)

#### 2. Narrated Diff (AI-Enhanced Code Review)

```tsx
<NarratedDiff>
  <DiffHeader>
    <FileStats>
      <Stat>+234 lines</Stat>
      <Stat>-89 lines</Stat>
      <Stat>3 files</Stat>
    </FileStats>
    <AIInsights>
      <Badge variant="success">Low Risk</Badge>
      <Badge variant="info">Test Coverage: 92%</Badge>
    </AIInsights>
  </DiffHeader>

  <NarrativeSummary>
    <SummaryCard>
      <Icon>📝</Icon>
      <Title>What Changed</Title>
      <BulletList>
        <li>Refactored authentication middleware</li>
        <li>Added JWT token validation</li>
        <li>Improved error handling</li>
      </BulletList>
    </SummaryCard>

    <SummaryCard>
      <Icon>⚠️</Icon>
      <Title>Risk Hotspots</Title>
      <BulletList>
        <li>auth.ts:42 - New crypto dependency</li>
        <li>middleware.ts:15 - Breaking API change</li>
      </BulletList>
    </SummaryCard>

    <SummaryCard>
      <Icon>🧪</Icon>
      <Title>Test Impact</Title>
      <BulletList>
        <li>3 new test files</li>
        <li>Coverage increased 87% → 92%</li>
        <li>All tests passing ✓</li>
      </BulletList>
    </SummaryCard>
  </NarrativeSummary>

  <DiffViewer>
    {/* Standard unified/split diff view */}
  </DiffViewer>
</NarratedDiff>
```

#### 3. Agent Crew Composer (Wizard)

```tsx
<CrewComposer>
  <WizardSteps>
    <Step active>1. Select Goal</Step>
    <Step>2. Choose Agents</Step>
    <Step>3. Configure</Step>
    <Step>4. Review & Launch</Step>
  </WizardSteps>

  {/* Step 1: Goal */}
  <GoalSelector>
    <GoalCard selected>
      <Icon>🚀</Icon>
      <Title>Ship MVP</Title>
      <Description>Plan, design, implement, test, deploy</Description>
    </GoalCard>
    <GoalCard>
      <Icon>🔧</Icon>
      <Title>Refactor Legacy</Title>
      <Description>Analyze, plan migration, incremental updates</Description>
    </GoalCard>
    <GoalCard>
      <Icon>🐛</Icon>
      <Title>Fix Incident</Title>
      <Description>Diagnose, patch, test, deploy hotfix</Description>
    </GoalCard>
  </GoalSelector>

  {/* Step 2: Agents (auto-populated based on goal) */}
  <AgentGrid>
    <AgentCard selected required>
      <Avatar>👷</Avatar>
      <Name>Chief Architect</Name>
      <Role>System Design</Role>
      <Badge>Required</Badge>
    </AgentCard>
    <AgentCard selected>
      <Avatar>📋</Avatar>
      <Name>Planner</Name>
      <Role>Requirements → Issues</Role>
      <Badge>Recommended</Badge>
    </AgentCard>
    {/* ... more agents */}
  </AgentGrid>

  {/* Step 3: Config */}
  <ConfigPanel>
    <BudgetSlider max={100} value={50}>
      <Label>Cost Budget: $50</Label>
    </BudgetSlider>
    <ModelPreference>
      <Select>
        <option>Balanced (Claude + GPT-5)</option>
        <option>Fast (Haiku + GPT-4o)</option>
        <option>Premium (Opus + GPT-5)</option>
      </Select>
    </ModelPreference>
  </ConfigPanel>

  {/* Step 4: Review */}
  <ReviewPanel>
    <ProjectionCard>
      <Metric label="Estimated Cost">$42-58</Metric>
      <Metric label="Estimated Time">2-3 hours</Metric>
      <Metric label="Agents">5 specialized</Metric>
    </ProjectionCard>
    <LaunchButton size="lg" variant="primary">
      Launch Crew 🚀
    </LaunchButton>
  </ReviewPanel>
</CrewComposer>
```

## Page Architectures

### Home Dashboard

```tsx
<HomePage>
  <Header>
    <Greeting>Good morning, Isaac</Greeting>
    <QuickActions>
      <Button>/spec new</Button>
      <Button>/review</Button>
    </QuickActions>
  </Header>

  <TodayStrip>
    <Card title="My PRs" count={3} />
    <Card title="My Specs" count={5} />
    <Card title="Failing Checks" count={1} variant="warning" />
  </TodayStrip>

  <AgentSignals>
    <SuggestionCard>
      <Title>PR #104 is ready for review</Title>
      <Actions>
        <Button>Review Now</Button>
        <Button>Later</Button>
      </Actions>
    </SuggestionCard>
    {/* ... more suggestions */}
  </AgentSignals>

  <PipelineHealth>
    <SparklineCard title="Latency (p95)" data={latencyData} />
    <SparklineCard title="Pass Rate" data={passRateData} />
    <SparklineCard title="Daily Spend" data={spendData} />
  </PipelineHealth>
</HomePage>
```

### Project Detail (Board View)

```tsx
<ProjectPage>
  <ProjectHeader>
    <Breadcrumb>Projects › {projectName}</Breadcrumb>
    <Tags>
      <Tag>Production</Tag>
      <Tag>High Priority</Tag>
    </Tags>
    <Actions>
      <Button>New Spec</Button>
      <Button>New PR</Button>
    </Actions>
  </ProjectHeader>

  <Tabs>
    <Tab active>Board</Tab>
    <Tab>Specs</Tab>
    <Tab>PRs</Tab>
    <Tab>Tests</Tab>
  </Tabs>

  <BoardView>
    <Column title="To Do" count={12}>
      <IssueCard>
        <Title>#54 Implement auth flow</Title>
        <Meta>
          <Assignee>Codegen Agent</Assignee>
          <Priority>High</Priority>
        </Meta>
      </IssueCard>
      {/* ... more cards */}
    </Column>

    <Column title="In Progress" count={5}>
      {/* ... */}
    </Column>

    <Column title="Review" count={3}>
      {/* ... */}
    </Column>

    <Column title="Done" count={28}>
      {/* ... */}
    </Column>
  </BoardView>
</ProjectPage>
```

### Analytics Dashboard

```tsx
<AnalyticsPage>
  <Filters>
    <TimeRangeSelect>Last 30 days</TimeRangeSelect>
    <ModelFilter>All Models</ModelFilter>
    <ProjectFilter>All Projects</ProjectFilter>
  </Filters>

  <KPIStrip>
    <KPI value="$127.42" change="-12%" trend="down" positive>
      Total Spend
    </KPI>
    <KPI value="89%" change="+4%" trend="up" positive>
      PR Merge Rate
    </KPI>
    <KPI value="42min" change="-8min" trend="down" positive>
      Avg MTTR
    </KPI>
  </KPIStrip>

  <ChartGrid>
    <Chart title="Cost by Model" type="bar">
      {/* Recharts */}
    </Chart>
    <Chart title="Agent Success Rate" type="line">
      {/* Recharts */}
    </Chart>
    <Chart title="Pipeline Health" type="area">
      {/* Recharts */}
    </Chart>
  </ChartGrid>
</AnalyticsPage>
```

## State Management

### Technology: Zustand + TanStack Query

```typescript
// Global UI state (Zustand)
interface UIStore {
  theme: 'light' | 'dark' | 'system';
  commandPaletteOpen: boolean;
  aiDockCollapsed: boolean;
  leftRailCollapsed: boolean;
}

// Server state (TanStack Query)
const { data: projects } = useQuery({
  queryKey: ['projects'],
  queryFn: fetchProjects,
  staleTime: 5 * 60 * 1000, // 5 min
})

// Real-time updates (WebSocket + Query invalidation)
useWebSocket('/ws/projects', {
  onMessage: (event) => {
    if (event.type === 'project.updated') {
      queryClient.invalidateQueries(['projects', event.projectId])
    }
  }
})
```

## Performance Targets

- **Initial Load**: <200ms (p95)
- **Route Transition**: <100ms
- **Command Palette**: <50ms to open
- **WebSocket Latency**: <100ms
- **Lighthouse Score**: >95

## Accessibility

- **WCAG 2.2 AA** compliance minimum
- **Keyboard Navigation**: All actions accessible via keyboard
- **Screen Readers**: Semantic HTML, ARIA labels
- **Focus Management**: Visible focus indicators, logical tab order
- **Reduced Motion**: Respect `prefers-reduced-motion`
- **High Contrast**: Minimum 4.5:1 contrast ratio

## Technology Stack

```json
{
  "framework": "Next.js 14 (App Router)",
  "language": "TypeScript 5.3",
  "styling": "Tailwind CSS 3.4",
  "components": "shadcn/ui + Radix UI",
  "state": "Zustand + TanStack Query",
  "forms": "React Hook Form + Zod",
  "charts": "Recharts",
  "icons": "Lucide React",
  "fonts": "General Sans, Inter, JetBrains Mono",
  "realtime": "WebSocket (Socket.io)",
  "testing": "Vitest + Playwright + Testing Library"
}
```

## File Structure

```
apps/web/
├── app/                      # Next.js App Router
│   ├── (auth)/               # Auth layout group
│   ├── (dashboard)/          # Main app layout
│   │   ├── layout.tsx        # Shell layout
│   │   ├── page.tsx          # Home
│   │   ├── projects/
│   │   ├── agents/
│   │   ├── analytics/
│   │   └── settings/
│   └── api/                  # API routes (BFF pattern)
├── components/
│   ├── ui/                   # shadcn/ui primitives
│   ├── app-shell/            # TopNav, LeftRail, AIDock
│   ├── command/              # Command Palette
│   ├── diff/                 # Narrated Diff
│   └── crew/                 # Crew Composer
├── lib/
│   ├── api/                  # API client
│   ├── hooks/                # Custom hooks
│   ├── stores/               # Zustand stores
│   └── utils/                # Helpers
└── styles/
    └── globals.css           # Tailwind + custom styles
```

## Next Steps

1. Review component specifications in [./modules/FRONTEND_COMPONENTS.md](./modules/FRONTEND_COMPONENTS.md)
2. See design tokens implementation in [./modules/DESIGN_TOKENS.md](./modules/DESIGN_TOKENS.md)
3. Read interaction patterns in [./modules/INTERACTION_PATTERNS.md](./modules/INTERACTION_PATTERNS.md)
