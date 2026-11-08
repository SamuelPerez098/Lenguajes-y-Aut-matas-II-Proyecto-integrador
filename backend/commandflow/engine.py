"""Fachada del pipeline: texto -> lexer -> parser -> semántico -> IR -> optimizador -> VM."""
from dataclasses import dataclass, field

from .ast_nodes import Program
from .errors import CommandFlowError, ExecutionError
from .ir import IRGenerator, Instr
from .lexer import tokenize
from .optimizer import Optimizer, OptimizationNote
from .parser import parse
from .semantic import SemanticAnalyzer, describe_instruction
from .services import EmailService, InMemoryEmailService
from .symbols import SymbolTable
from .vm import Output, StateChange, Trace, VirtualMachine


@dataclass
class CompilationResult:
    errors: list = field(default_factory=list)
    tokens: list = field(default_factory=list)
    ast: Program | None = None
    instructions: list = field(default_factory=list)      # acciones semánticas (dicts)
    ir: list = field(default_factory=list)
    optimized_ir: list = field(default_factory=list)
    optimizations: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class RunResult:
    ok: bool
    errors: list
    outputs: list
    events: list
    compilation: CompilationResult

    @property
    def message(self) -> str:
        if self.errors:
            return "\n".join(e.format() for e in self.errors)
        if not self.compilation.ast.instructions:
            return "Nada que ejecutar."
        if not self.outputs and not self.events:
            return "Sin cambios: los dispositivos ya estaban en el estado solicitado."
        return "OK"


class CommandFlow:
    def __init__(self, table: SymbolTable | None = None, email_service: EmailService | None = None,
                 optimize: bool = True, optimizer: Optimizer | None = None):
        self.table = table or SymbolTable.default()
        self.email_service = email_service or InMemoryEmailService()
        self.optimize = optimize
        self.optimizer = optimizer or Optimizer()

    def compile(self, source: str) -> CompilationResult:
        result = CompilationResult()
        try:
            result.tokens = tokenize(source)
            result.ast = parse(result.tokens)
        except CommandFlowError as exc:        # léxico o sintáctico: se detiene en el primero
            result.errors = [exc]
            return result
        errors = SemanticAnalyzer(self.table).analyze(result.ast)
        if errors:                              # semántico: se reportan todos
            result.errors = errors
            return result
        result.instructions = [describe_instruction(n) for n in result.ast.instructions]
        result.ir = IRGenerator().generate(result.ast)
        if self.optimize:
            opt = self.optimizer.optimize(result.ir)
            result.optimized_ir, result.optimizations = opt.code, opt.notes
        else:
            result.optimized_ir = list(result.ir)
        return result

    def run(self, source: str) -> RunResult:
        comp = self.compile(source)
        if not comp.ok:   # nada se ejecuta si el programa tiene algún error
            return RunResult(False, comp.errors, [], [], comp)
        vm = VirtualMachine(self.table, self.email_service)
        try:
            trace = vm.run(comp.optimized_ir)
            return RunResult(True, [], trace.outputs, trace.events, comp)
        except ExecutionError as exc:
            return RunResult(False, [exc], vm.trace.outputs, vm.trace.events, comp)
