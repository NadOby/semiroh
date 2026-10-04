import java.util.List;
import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import edu.mit.csail.sdg.alloy4.A4Reporter;
import edu.mit.csail.sdg.alloy4.ErrorWarning;
import edu.mit.csail.sdg.ast.Command;
import edu.mit.csail.sdg.parser.CompModule;
import edu.mit.csail.sdg.parser.CompUtil;
import edu.mit.csail.sdg.translator.A4Options;
import edu.mit.csail.sdg.translator.A4Solution;
import edu.mit.csail.sdg.translator.TranslateAlloyToKodkod;
import kodkod.engine.satlab.SATFactory;

/**
 * Headless Alloy runner for semantic-core verification experiments.
 *
 * Usage:
 *
 *   AlloyRunner <model> <command-index> <solver> <decompose-mode> <threads>
 *
 * decompose-mode:
 *   0 = batch/off
 *   1 = hybrid
 *   2 = parallel
 *
 * The runner uses Alloy's normal parser and
 * TranslateAlloyToKodkod.execute_commandFromBook entry point while exposing
 * decomposition controls and detailed execution instrumentation.
 *
 * Instrumentation is observational. It must not alter the command, scopes,
 * solver configuration, or expected result.
 */
public final class AlloyRunner {

    private static final long HEARTBEAT_SECONDS = 60;

    private AlloyRunner() {
    }

    public static void main(String[] args) throws Exception {
        long processStartNanos = System.nanoTime();

        if (args.length != 5) {
            usage();
            System.exit(2);
        }

        String model = args[0];
        int commandIndex = parseInt(args[1], "command-index");
        String solverId = args[2];
        int decomposeMode = parseInt(args[3], "decompose-mode");
        int threads = parseInt(args[4], "threads");

        if (commandIndex < 0) {
            fail("command-index must be >= 0");
        }

        if (decomposeMode < 0 || decomposeMode > 2) {
            fail("decompose-mode must be 0, 1, or 2");
        }

        if (threads < 1) {
            fail("threads must be >= 1");
        }

        Optional<SATFactory> solverResult = SATFactory.find(solverId);

        if (solverResult.isEmpty()) {
            fail("unknown Alloy solver: " + solverId);
        }

        SATFactory solver = solverResult.get();

        InstrumentationReporter reporter =
            new InstrumentationReporter(processStartNanos);

        printRuntimeEnvironment();
        printSolverMetadata(solver);

        long parseStartNanos = System.nanoTime();

        CompModule world = CompUtil.parseEverything_fromFile(
            reporter,
            null,
            model
        );

        long parseElapsedNanos = System.nanoTime() - parseStartNanos;

        metric(
            "phase=parse"
                + " wall_ms=" + nanosToMillis(parseElapsedNanos)
        );

        List<Command> commands = world.getAllCommands();

        if (commandIndex >= commands.size()) {
            fail(
                "command-index "
                    + commandIndex
                    + " is outside available range 0.."
                    + (commands.size() - 1)
            );
        }

        Command command = commands.get(commandIndex);

        printCommandMetadata(
            model,
            commandIndex,
            command
        );

        if (command.expects != 0 && command.expects != 1) {
            fail(
                "verification command must declare "
                    + "expect 0 or expect 1"
            );
        }

        A4Options options = new A4Options();
        options.originalFilename = model;
        options.solver = solver;
        options.decompose_mode = decomposeMode;
        options.decompose_threads = threads;

        printOptions(options);

        long executeStartNanos = System.nanoTime();
        reporter.setExecutionStartNanos(executeStartNanos);

        ScheduledExecutorService heartbeat =
            startHeartbeat(executeStartNanos);

        A4Solution solution;

        try {
            solution =
                TranslateAlloyToKodkod.execute_commandFromBook(
                    reporter,
                    world.getAllReachableSigs(),
                    command,
                    options
                );
        } catch (Exception | Error ex) {
            metric(
                "event=exception"
                    + " elapsed_ms="
                    + nanosToMillis(System.nanoTime() - executeStartNanos)
                    + " type="
                    + token(ex.getClass().getName())
                    + " message="
                    + quoted(ex.getMessage())
            );
            throw ex;
        } finally {
            stopHeartbeat(heartbeat);
        }

        long executeElapsedNanos =
            System.nanoTime() - executeStartNanos;

        long totalElapsedNanos =
            System.nanoTime() - processStartNanos;

        boolean satisfiable = solution.satisfiable();
        String result = satisfiable ? "SAT" : "UNSAT";

        metric(
            "phase=execute"
                + " wall_ms="
                + nanosToMillis(executeElapsedNanos)
        );

        metric(
            "phase=total"
                + " wall_ms="
                + nanosToMillis(totalElapsedNanos)
        );

        metric(
            "event=final"
                + " result=" + result
                + " expected="
                + expectationName(command.expects)
                + " reporter_translate_events="
                + reporter.translateEvents()
                + " reporter_cnf_events="
                + reporter.cnfEvents()
                + " reporter_result_events="
                + reporter.resultEvents()
        );

        printMemory("final");

        if (command.expects == 1 && !satisfiable) {
            fail("expected SAT but solver returned UNSAT");
        }

        if (command.expects == 0 && satisfiable) {
            fail("expected UNSAT but solver returned SAT");
        }
    }

    private static void printRuntimeEnvironment() {
        Runtime runtime = Runtime.getRuntime();

        metric(
            "event=runtime"
                + " java_version="
                + token(System.getProperty("java.version"))
                + " vm="
                + quoted(System.getProperty("java.vm.name"))
                + " processors="
                + runtime.availableProcessors()
                + " heap_max_mb="
                + bytesToMiB(runtime.maxMemory())
        );

        printMemory("startup");
    }

    private static void printSolverMetadata(SATFactory solver) {
        metric(
            "event=solver"
                + " id=" + token(solver.id())
                + " name=" + quoted(solver.name())
                + " type=" + token(solver.type())
                + " incremental=" + solver.incremental()
                + " prover=" + solver.prover()
                + " maxsat=" + solver.maxsat()
                + " unbounded=" + solver.unbounded()
                + " description="
                + quoted(solver.getDescription().orElse(""))
        );
    }

    private static void printCommandMetadata(
        String model,
        int commandIndex,
        Command command
    ) {
        metric(
            "event=command"
                + " model=" + quoted(model)
                + " index=" + commandIndex
                + " kind=" + (command.check ? "check" : "run")
                + " label=" + quoted(command.label)
                + " expected="
                + expectationName(command.expects)
                + " overall_scope=" + command.overall
                + " bitwidth=" + command.bitwidth
                + " maxseq=" + command.maxseq
                + " scope_count=" + command.scope.size()
                + " command=" + quoted(command.toString())
        );
    }

    private static void printOptions(A4Options options) {
        metric(
            "event=options"
                + " solver=" + token(options.solver.id())
                + " symmetry=" + options.symmetry
                + " skolem_depth=" + options.skolemDepth
                + " infer_partial_instance="
                + options.inferPartialInstance
                + " no_overflow=" + options.noOverflow
                + " unrolls=" + options.unrolls
                + " core_minimization="
                + options.coreMinimization
                + " core_granularity="
                + options.coreGranularity
                + " record_kodkod="
                + options.recordKodkod
                + " decompose_mode="
                + options.decompose_mode
                + " decompose_mode_name="
                + modeName(options.decompose_mode)
                + " decompose_threads="
                + options.decompose_threads
        );
    }

    private static ScheduledExecutorService startHeartbeat(
        long executionStartNanos
    ) {
        ScheduledExecutorService scheduler =
            Executors.newSingleThreadScheduledExecutor(
                runnable -> {
                    Thread thread =
                        new Thread(runnable, "alloy-heartbeat");
                    thread.setDaemon(true);
                    return thread;
                }
            );

        scheduler.scheduleAtFixedRate(
            () -> {
                long elapsedNanos =
                    System.nanoTime() - executionStartNanos;

                Runtime runtime = Runtime.getRuntime();
                long used =
                    runtime.totalMemory()
                        - runtime.freeMemory();

                System.out.printf(
                    "ALLOY_HEARTBEAT "
                        + "elapsed_s=%.1f "
                        + "heap_used_mb=%d "
                        + "heap_committed_mb=%d "
                        + "heap_max_mb=%d%n",
                    elapsedNanos / 1_000_000_000.0,
                    bytesToMiB(used),
                    bytesToMiB(runtime.totalMemory()),
                    bytesToMiB(runtime.maxMemory())
                );

                System.out.flush();
            },
            HEARTBEAT_SECONDS,
            HEARTBEAT_SECONDS,
            TimeUnit.SECONDS
        );

        return scheduler;
    }

    private static void stopHeartbeat(
        ScheduledExecutorService scheduler
    ) {
        scheduler.shutdownNow();

        try {
            scheduler.awaitTermination(
                5,
                TimeUnit.SECONDS
            );
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
        }
    }

    private static void printMemory(String point) {
        Runtime runtime = Runtime.getRuntime();

        long used =
            runtime.totalMemory()
                - runtime.freeMemory();

        metric(
            "event=memory"
                + " point=" + token(point)
                + " heap_used_mb=" + bytesToMiB(used)
                + " heap_committed_mb="
                + bytesToMiB(runtime.totalMemory())
                + " heap_max_mb="
                + bytesToMiB(runtime.maxMemory())
        );
    }

    private static int parseInt(
        String value,
        String name
    ) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException ex) {
            fail(name + " must be an integer: " + value);
            return 0;
        }
    }

    private static String modeName(int mode) {
        return switch (mode) {
            case 0 -> "batch";
            case 1 -> "hybrid";
            case 2 -> "parallel";
            default -> "unknown";
        };
    }

    private static String expectationName(int expects) {
        return switch (expects) {
            case 0 -> "UNSAT";
            case 1 -> "SAT";
            default -> "unspecified";
        };
    }

    private static long nanosToMillis(long nanos) {
        return TimeUnit.NANOSECONDS.toMillis(nanos);
    }

    private static long bytesToMiB(long bytes) {
        return bytes / (1024L * 1024L);
    }

    private static String token(String value) {
        if (value == null || value.isBlank()) {
            return "-";
        }

        return value
            .replaceAll("\\s+", "_")
            .replace("=", "_");
    }

    private static String quoted(String value) {
        if (value == null) {
            return "\"\"";
        }

        return "\""
            + value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\r", "\\r")
                .replace("\n", "\\n")
            + "\"";
    }

    private static void metric(String message) {
        System.out.println(
            "ALLOY_METRIC " + message
        );
        System.out.flush();
    }

    private static void trace(String message) {
        System.out.println(
            "ALLOY_TRACE " + message
        );
        System.out.flush();
    }

    private static void usage() {
        System.err.println(
            "Usage: AlloyRunner "
                + "<model> <command-index> <solver> "
                + "<decompose-mode> <threads>"
        );
    }

    private static void fail(String message) {
        System.err.println(
            "ERROR: " + message
        );
        System.err.flush();
        System.exit(1);
    }

    private static final class InstrumentationReporter
        extends A4Reporter {

        private final long processStartNanos;

        private final AtomicInteger translateCount =
            new AtomicInteger();

        private final AtomicInteger cnfCount =
            new AtomicInteger();

        private final AtomicInteger resultCount =
            new AtomicInteger();

        private volatile long executionStartNanos = -1L;

        InstrumentationReporter(long processStartNanos) {
            this.processStartNanos = processStartNanos;
        }

        void setExecutionStartNanos(
            long executionStartNanos
        ) {
            this.executionStartNanos =
                executionStartNanos;
        }

        int translateEvents() {
            return translateCount.get();
        }

        int cnfEvents() {
            return cnfCount.get();
        }

        int resultEvents() {
            return resultCount.get();
        }

        @Override
        public void warning(ErrorWarning warning) {
            trace(
                "event=warning"
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " message="
                    + quoted(warning.toString())
            );
        }

        @Override
        public void scope(String message) {
            trace(
                "event=scope"
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " message="
                    + quoted(message)
            );
        }

        @Override
        public void bound(String message) {
            trace(
                "event=bound"
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " message="
                    + quoted(message)
            );
        }

        @Override
        public void translate(
            String solver,
            int bitwidth,
            int maxseq,
            int mintrace,
            int maxtrace,
            int skolemDepth,
            int symmetry,
            String strategy
        ) {
            int event = translateCount.incrementAndGet();

            metric(
                "event=translate"
                    + " sequence=" + event
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " solver="
                    + token(solver)
                    + " bitwidth=" + bitwidth
                    + " maxseq=" + maxseq
                    + " mintrace=" + mintrace
                    + " maxtrace=" + maxtrace
                    + " skolem_depth="
                    + skolemDepth
                    + " symmetry=" + symmetry
                    + " strategy="
                    + quoted(strategy)
            );
        }

        @Override
        public void solve(
            int plength,
            int primaryVars,
            int totalVars,
            int clauses
        ) {
            int event = cnfCount.incrementAndGet();

            metric(
                "event=cnf"
                    + " sequence=" + event
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " prefix_length="
                    + plength
                    + " primary_vars="
                    + primaryVars
                    + " total_vars="
                    + totalVars
                    + " clauses="
                    + clauses
            );
        }

        @Override
        public void resultSAT(
            Object command,
            long solvingTime,
            Object solution
        ) {
            result(
                "SAT",
                command,
                solvingTime
            );
        }

        @Override
        public void resultUNSAT(
            Object command,
            long solvingTime,
            Object solution
        ) {
            result(
                "UNSAT",
                command,
                solvingTime
            );
        }

        @Override
        public void minimizing(
            Object command,
            int before
        ) {
            metric(
                "event=core_minimization_start"
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " before=" + before
                    + " command="
                    + quoted(String.valueOf(command))
            );
        }

        @Override
        public void minimized(
            Object command,
            int before,
            int after
        ) {
            metric(
                "event=core_minimization_end"
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " before=" + before
                    + " after=" + after
                    + " command="
                    + quoted(String.valueOf(command))
            );
        }

        private void result(
            String result,
            Object command,
            long solvingTime
        ) {
            int event = resultCount.incrementAndGet();

            metric(
                "event=solver_result"
                    + " sequence=" + event
                    + " elapsed_ms="
                    + elapsedMillis()
                    + " result=" + result
                    + " alloy_reported_ms="
                    + solvingTime
                    + " command="
                    + quoted(String.valueOf(command))
            );
        }

        private long elapsedMillis() {
            long start =
                executionStartNanos >= 0
                    ? executionStartNanos
                    : processStartNanos;

            return nanosToMillis(
                System.nanoTime() - start
            );
        }
    }
}
