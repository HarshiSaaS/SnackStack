

1. Overview

SnackStack is a voice-enabled multi-agent food delivery assistant powered by LangGraph. The system accepts user queries (text or voice), 
routes them through an orchestrator to specialist agents (Menu Agent and Order Agent), and returns a unified response.

This project covers core concepts in modern AI application development: multi-agent orchestration, 
RAG (Retrieval-Augmented Generation), structured LLM output, tool calling, human-in-the-loop interaction, and voice I/O.


2. What Are We Building
- A CLI-based assistant for a fictional food delivery platform called SnackStack. The system should:
- Accept natural language queries via text input (and optionally voice)
- Route queries to the correct specialist agent(s) using an LLM-powered orchestrator
- Search a menu catalog using semantic search (RAG with ChromaDB)
- Look up order status by Order ID, Tracking ID, or email
- Ask the user for missing information when needed (Human-in-the-Loop)
- Merge responses from multiple agents into a single friendly reply
- Support voice input (Whisper STT) and voice output (OpenAI TTS)


2. Architecture Diagram

Voice / Text Input
        |
        v
  +-------------+
  | Orchestrator |  <-- Structured-output routing (Pydantic)
  +------+------+
         |  Send() -- parallel dispatch (optional)
    +----+-----+
    v          v
 +--------+ +--------+
 |  Menu  | | Order  |  <-- Each runs its own tool-calling loop
 | Agent  | | Agent  |
 +---+----+ +---+----+
     |          |
     v          v
   +--------------+
   | Synthesizer  |  <-- Merges responses (optional)
   +------+-------+
          |
          v
   Voice / Text Output

3. Functional Requirements

3.1 Orchestrator (Query Router)
- Use an LLM with structured output (Pydantic schema) to classify each user query
- Route to menu_agent for food/menu queries and general greetings
- Route to order_agent for order tracking queries
- Route to both agents in parallel when the query spans both topics (Optional: use Send() for parallel dispatch, or route sequentially)
- Default to menu_agent when intent is unclear

3.2 Menu Agent (RAG-Powered)
- Build a vector store from a menu catalog of 8 dishes using ChromaDB
- Use OpenAI embeddings (text-embedding-3-small) for semantic search
- Implement a search_menu_catalog tool that the LLM calls via tool binding
- Run an internal tool-calling loop (LLM decides when to call tools and when to respond)
- Handle greetings and general conversation warmly

3.3 Order Agent (with Human-in-the-Loop)
- Support order lookup by Order ID (e.g. ORD-201), Tracking ID (e.g. SS201TRK), or email
- Extract identifiers from the user query using regex patterns
- If no identifier is found, use LangGraph's interrupt() to pause the graph and ask the user
- Resume execution with Command(resume=user_input) after the user provides an identifier
- Run an internal tool-calling loop identical in pattern to the Menu Agent

3.4 Synthesizer (Optional)
- If you implement parallel dispatch to both agents, you will need a synthesizer to merge their outputs. If you route to one agent at a time, the agent's response can be used directly as the final answer.
- Receive outputs from one or both agents
- Use an LLM to merge them into a single, coherent, friendly reply
- If only one agent responded, clean up and present that response directly

3.5 Voice I/O (Optional / Bonus)
- Voice Input: Record audio via sounddevice, transcribe with OpenAI Whisper
- Voice Output: Generate speech with OpenAI TTS, play through speaker via sounddevice
- Support --voice (full voice), --voice-out (text in, voice out), and text-only modes

4. Data You Will Work With
4.1 Menu Catalog (8 dishes)

4.2 Order Database (5 orders)
Each order has: order_id, item_id, item_name, customer_name, customer_email, status, price, order_date, estimated_delivery, and tracking_id. 
Define as a Python dictionary keyed by order_id.

5. Expected Project Structure
Organize your code in the following modular layout. A sample structure is provided below for reference — you are not restricted to follow it exactly. Feel free to rename files, reorganize modules, or add additional files as you see fit, as long as the core functionality works and the code remains clean and modular.
snackstack/
|-- snackstack/           # Python package
|   |-- __init__.py
|   |-- main.py           # CLI entry point
|   |-- config.py         # LLM, embeddings, OpenAI client setup
|   |-- state.py          # Shared StackState (TypedDict)
|   |-- graph.py          # StateGraph builder & compiler
|   |-- logger.py         # Centralized logging
|   |
|   |-- agents/
|   |   |-- __init__.py   # Re-exports node functions
|   |   |-- prompts.py    # System prompts for all nodes
|   |   |-- orchestrator.py
|   |   |-- menu_agent.py
|   |   |-- order_agent.py
|   |   |-- synthesizer.py  # Optional: merges parallel responses
|   |
|   |-- data/
|   |   |-- __init__.py
|   |   |-- menu.py       # Menu catalog
|   |   |-- orders.py     # Order database
|   |
|   |-- tools/
|   |   |-- __init__.py
|   |   |-- rag.py        # ChromaDB vector store
|   |   |-- menu_tools.py # search_menu_catalog
|   |   |-- order_tools.py# get_order_status
|   |
|   |-- voice/            # Optional
|       |-- __init__.py
|       |-- recorder.py   # Whisper STT
|       |-- speaker.py    # OpenAI TTS
|
|-- pyproject.toml
|-- .env.example
|-- .gitignore
|-- README.md

6. Step-by-Step Implementation Guide
Follow these phases in order. Each phase builds on the previous one and produces a testable milestone.

Phase 1: Project Setup & Config
Goal: 
Get LLM responding, and a basic graph compiling.


Create the project folder structure as shown above
Write pyproject.toml with project metadata, dependencies, and [project.scripts] entry
Create config.py: load OPENAI_API_KEY from environment, initialize ChatOpenAI (gpt-4o) and OpenAIEmbeddings
Create logger.py with a setup_logger() function using Python's logging module
Create state.py with a StackState TypedDict containing: messages, user_query, route, menu_response, order_response, final_answer


Phase 2: Data & RAG
Goal: 
Build the menu vector store and verify semantic search works.


Define the menu catalog in data/menu.py as a list of 8 dish dictionaries
Define the order database in data/orders.py as a dictionary of 5 orders
Build tools/rag.py: convert menu items to LangChain Documents, create a ChromaDB vector store, expose a retriever
Build tools/menu_tools.py: create a @tool function search_menu_catalog that uses the retriever
Build tools/order_tools.py: create a @tool function get_order_status that searches by order ID, tracking ID, or email
Verify: import the tools and test them directly with sample inputs

Phase 3: Agents
Goal: 
Build each agent as a standalone node function that can be tested independently.


Write system prompts in agents/prompts.py for: Orchestrator, Menu Agent, Order Agent, and optionally Synthesizer
Build the Orchestrator: use llm.with_structured_output() with a Pydantic model that returns a list of agent names + reasoning
Build the Menu Agent: bind tools to LLM, run a tool-calling loop (max 5 iterations), return Command(goto='synthesizer_node')
Build the Order Agent: same pattern as Menu Agent, but add identifier extraction with regex and interrupt() when no ID is found
(Optional) Build the Synthesizer: combine agent outputs, pass to LLM for final cleanup. Needed if you implement parallel dispatch
Verify: test each agent function by passing a mock StackState dictionary

Phase 4: Graph Assembly
Goal: 
Wire everything into a working LangGraph StateGraph.


In graph.py: create a StateGraph(StackState), add all nodes, add edges (START -> orchestrator, final node -> END)
(Optional) The orchestrator uses Command + Send() to dispatch to agents in parallel. Alternatively, route to one agent at a time using conditional edges
Compile with MemorySaver checkpointer for multi-turn conversation memory
Verify: invoke the graph with a test query and check the final_answer in the result

Phase 5: CLI & HITL
Goal: 
Build the interactive text loop with interrupt handling.


In main.py: create a SnackStackAssistant class that wraps the compiled graph
Implement the ask() method: invoke the graph, then check graph.get_state() for pending interrupts
For each interrupt: show the question via input(), collect the answer, resume with Command(resume=answer)
Build run_text_loop(): a REPL that reads input, calls ask(), and logs the response
Add reset and quit commands
Wire up the main() entry point with argparse


Phase 6: Voice I/O (Bonus)
Goal: 
Add mic recording + speaker playback for a two-way voice conversation.


Build voice/recorder.py: use sounddevice to record audio, soundfile to encode WAV, OpenAI Whisper to transcribe
Build voice/speaker.py: request wav format from OpenAI TTS, decode with soundfile, play with sounddevice
Add --voice and --voice-out CLI flags



7. Key Concepts to Understand

A. StateGraph + Send() - LangGraph's core abstraction. Send() enables parallel dispatch to multiple agents from the orchestrator. (Optional: you can route sequentially instead.)
B. Structured Output - 
llm.with_structured_output(PydanticModel) forces the LLM to return a validated schema instead of free text.
C. Tool Calling Loop
D. Bind tools to LLM with llm.bind_tools(). In a loop: invoke LLM, check for tool_calls, execute tools, append results, repeat until LLM gives a text answer.
E.RAG - Convert menu data to Documents, embed with OpenAI, store in ChromaDB, retrieve with semantic similarity.
F.Human-in-the-Loop - interrupt() pauses the graph and surfaces a question to the caller. Command(resume=value) continues execution.
G. MemorySaver - In-memory checkpointer that enables multi-turn conversation by persisting state across invocations.
H. Command + goto - LangGraph's way for a node to control the next step. Command(goto='node') replaces conditional edges.

8. Testing Checklist

9. Common Pitfalls
- Circular imports: Use the package-qualified imports (from snackstack.config import llm), not bare imports
- Orchestrator routing both agents for simple greetings: Add explicit rules in the prompt for greetings/general chat
- Tool-calling infinite loop: Always set a MAX_TOOL_ITERATIONS cap and handle the fallback
- HITL not working: The checkpointer (MemorySaver) is required for interrupt() to work. Make sure graph.compile(checkpointer=memory)
- Voice not playing: Request wav format from TTS API (not mp3) so soundfile can decode it in-memory
- ChromaDB warnings: These are normal on first run. The in-memory store rebuilds each time the app starts

