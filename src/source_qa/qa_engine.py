"""Question-Answering engine using Moonshot AI."""

from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

from source_qa.config import get_settings
from source_qa.indexer import CodeIndexer
from source_qa.retriever import CodeRetriever, RetrievedChunk

console = Console()


class CodeQASystem:
    """Main QA system for source code."""

    SYSTEM_PROMPT = """You are a helpful coding assistant. You have access to relevant source code 
context to answer questions. When answering:

1. Base your answers on the provided code context
2. Reference specific files and line numbers when applicable
3. Explain the code clearly and concisely
4. If the context doesn't contain enough information, say so
5. Provide code examples when helpful

Always cite the source files you reference in your answer."""

    def __init__(self):
        settings = get_settings()
        
        if not settings.moonshot_api_key:
            raise ValueError(
                "Moonshot API key not configured. "
                "Set MOONSHOT_API_KEY environment variable or configure .kimi.toml"
            )
        
        self.client = OpenAI(
            api_key=settings.moonshot_api_key,
            base_url=settings.moonshot_base_url,
        )
        self.model = settings.moonshot_model
        
        self.indexer = CodeIndexer()
        self.retriever = CodeRetriever()

    def index_directory(self, directory: str, clear_existing: bool = False) -> dict:
        """Index a directory of source code."""
        return self.indexer.index_directory(directory, clear_existing)

    def query(
        self,
        question: str,
        top_k: int = 5,
        stream: bool = False,
        verbose: bool = False,
    ) -> str:
        """Query the QA system with a question."""
        # Retrieve relevant chunks
        chunks = self.retriever.retrieve(question, top_k=top_k)
        
        if verbose:
            console.print(f"[dim]Retrieved {len(chunks)} relevant chunks[/dim]")
            for chunk in chunks:
                console.print(
                    f"[dim]  - {chunk.file_path} ({chunk.score:.3f})[/dim]"
                )

        # Format context
        context = self.retriever.format_context(chunks)
        
        # Build messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ]

        # Call Moonshot API
        if stream:
            return self._stream_response(messages)
        else:
            return self._complete_response(messages)

    def _complete_response(self, messages: list[dict]) -> str:
        """Get complete response from API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _stream_response(self, messages: list[dict]) -> str:
        """Stream response from API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            stream=True,
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                console.print(content, end="")
        
        console.print()  # New line after streaming
        return full_response

    def chat(self, verbose: bool = False) -> None:
        """Start an interactive chat session."""
        console.print("[bold green]Source Code QA System[/bold green]")
        console.print("[dim]Type 'quit', 'exit', or press Ctrl+C to exit[/dim]")
        console.print()
        
        conversation_history = []
        
        while True:
            try:
                question = console.input("[bold blue]You:[/bold blue] ").strip()
                
                if question.lower() in ("quit", "exit", "q"):
                    break
                
                if not question:
                    continue

                # Retrieve context
                chunks = self.retriever.retrieve(question)
                context = self.retriever.format_context(chunks)
                
                if verbose:
                    console.print(f"[dim]Using {len(chunks)} context chunks[/dim]")

                # Build messages with history
                messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
                messages.extend(conversation_history[-6:])  # Keep last 3 exchanges
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                })

                # Get response
                console.print("[bold green]Assistant:[/bold green] ", end="")
                response = self._stream_response(messages)
                
                # Update history
                conversation_history.append({"role": "user", "content": question})
                conversation_history.append({"role": "assistant", "content": response})
                console.print()

            except KeyboardInterrupt:
                console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
