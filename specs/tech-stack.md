# BookWorm Engineer - Tech Stack

## Core Technology Stack

### Backend Framework
- **Python 3.10+** - Primary programming language
- **LangChain** - Orchestrates LLM interactions and tool integrations
- **OpenAI API** - LLM provider via OpenRouter for unified access

### Vector Database & RAG
- **ChromaDB** - Lightweight vector database for document storage
- **sentence-transformers** - Embedding model for semantic search
- **langchain-chroma** - ChromaDB integration with LangChain
- **langchain-text-splitters** - Document chunking for RAG

### CLI Interface
- **Click** (via opencode inspiration) - Command-line interface framework
- **python-dotenv** - Environment variable management

### Project Management
- **Git** - Version control integration
- **Pathlib** - Cross-platform path handling

### Optional Dependencies
- **pytest** - Testing framework (dev dependency)

## Key Technical Decisions

### 1. OpenRouter Integration
**Decision**: Use OpenRouter as the LLM API gateway

**Rationale**:
- Provides unified access to multiple LLM providers
- Reduces vendor lock-in
- Offers cost-effective pricing tiers
- Simplifies API key management

### 2. ChromaDB for Vector Storage
**Decision**: Choose ChromaDB over other vector databases

**Rationale**:
- Lightweight and easy to deploy
- Good performance for small to medium datasets
- Simple API integration with LangChain
- No external dependencies or complex setup

### 3. Three-Mode Architecture
**Decision**: Implement plan/build/research modes

**Rationale**:
- Separates concerns for better user experience
- Allows specialized behavior for different task types
- Provides clear mental model for users
- Enables progressive disclosure of capabilities

### 4. File-based State Management
**Decision**: Use AGENTS.md and PROGRESS.md for project state

**Rationale**:
- Simple and human-readable
- No database overhead
- Works offline
- Easy to version control

### 5. Tool-based Architecture
**Decision**: Use LangChain tools for all operations

**Rationale**:
- Enables consistent tool interface
- Leverages LangChain ecosystem
- Easy to add new capabilities
- Supports complex tool chains

## Architecture Patterns

### 1. Agent-Based Design
- **Pattern**: Single agent with configurable modes
- **Benefits**: Consistent interface, centralized state management
- **Implementation**: `Agent` class in `agent.py`

### 2. Command Pattern
- **Pattern**: Structured command handling
- **Benefits**: Extensible command system, clean separation of concerns
- **Implementation**: `commands.py` with `CommandResult` enum

### 3. Tool Registry Pattern
- **Pattern**: Dynamic tool registration and discovery
- **Benefits**: Pluggable architecture, runtime tool management
- **Implementation**: `ToolRegistry` in `tools/registry.py`

### 4. Configuration-Driven Design
- **Pattern**: All configuration via environment variables
- **Benefits**: Environment-agnostic, easy deployment
- **Implementation**: `Config` dataclass in `config.py`

## Performance Considerations

### 1. Context Window Management
- **Strategy**: Monitor token usage and warn at 75% threshold
- **Implementation**: `HALLUNCINATION_THRESHOLD` constant in `agent.py`

### 2. Efficient RAG
- **Strategy**: Configurable chunk size (800 chars) with 120 overlap
- **Implementation**: `rag_chunk_size` and `rag_chunk_overlap` config values

### 3. Memory Management
- **Strategy**: Keep only necessary context in message history
- **Implementation**: Streamlined message passing in agent loop

## Security Considerations

### 1. Environment Variables
- **Strategy**: All secrets via `.env` file
- **Implementation**: `python-dotenv` with required/optional variables

### 2. API Key Management
- **Strategy**: OpenRouter API keys, no direct LLM provider keys
- **Implementation**: Single `LLM_API_KEY` environment variable

### 3. File System Access
- **Strategy**: Restricted to project directory only
- **Implementation**: `working_dir` config parameter

## Future Technical Directions

### 1. Multi-Model Support
- Add support for additional LLM providers
- Implement model selection strategies

### 2. Advanced RAG
- Implement query rewriting
- Add document ranking improvements

### 3. Web Integration
- Add web-based UI option
- Implement real-time collaboration features

### 4. Plugin Architecture
- Make tools fully pluggable
- Add community tool marketplace

## Development Guidelines

### 1. Code Style
- Use type hints throughout
- Follow PEP 8 conventions
- Write comprehensive docstrings

### 2. Testing Strategy
- Unit tests for all core functionality
- Integration tests for tool chains
- End-to-end tests for user workflows

### 3. Documentation
- Maintain AGENTS.md with project patterns
- Keep PROGRESS.md for implementation tracking
- Document all tool behaviors and limitations