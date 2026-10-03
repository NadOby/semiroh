import java.util.List;
import java.util.Optional;

import edu.mit.csail.sdg.alloy4.A4Reporter;
import edu.mit.csail.sdg.ast.Command;
import edu.mit.csail.sdg.parser.CompModule;
import edu.mit.csail.sdg.parser.CompUtil;
import edu.mit.csail.sdg.translator.A4Options;
import edu.mit.csail.sdg.translator.A4Solution;
import edu.mit.csail.sdg.translator.TranslateAlloyToKodkod;
import kodkod.engine.satlab.SATFactory;

/**
 * Minimal headless Alloy runner for semantic-core verification experiments.
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
 * This deliberately uses the same Alloy parser and
 * TranslateAlloyToKodkod.execute_commandFromBook entry point as the stock
 * Alloy CLI. It additionally exposes A4Options.decompose_mode and
 * decompose_threads, which Alloy 6.2.0's CLI does not expose.
 */
public final class AlloyRunner {

    private AlloyRunner() {
    }

    public static void main(String[] args) throws Exception {
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

        Optional<SATFactory> solver = SATFactory.find(solverId);

        if (solver.isEmpty()) {
            fail("unknown Alloy solver: " + solverId);
        }

        CompModule world = CompUtil.parseEverything_fromFile(
            A4Reporter.NOP,
            null,
            model
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

        A4Options options = new A4Options();
        options.originalFilename = model;
        options.solver = solver.get();
        options.decompose_mode = decomposeMode;
        options.decompose_threads = threads;

        System.out.println("Model: " + model);
        System.out.println("Command index: " + commandIndex);
        System.out.println("Command: " + command);
        System.out.println("Solver: " + solverId);
        System.out.println("Decompose mode: " + modeName(decomposeMode));
        System.out.println("Decompose threads: " + threads);
        System.out.println("Expected: " + expectationName(command.expects));

        long start = System.nanoTime();

        A4Solution solution =
            TranslateAlloyToKodkod.execute_commandFromBook(
                A4Reporter.NOP,
                world.getAllReachableSigs(),
                command,
                options
            );

        long elapsedNanos = System.nanoTime() - start;
        double elapsedSeconds = elapsedNanos / 1_000_000_000.0;

        boolean satisfiable = solution.satisfiable();

        System.out.println(
            "Result: " + (satisfiable ? "SAT" : "UNSAT")
        );
        System.out.printf(
            "Elapsed: %.3f s%n",
            elapsedSeconds
        );

        if (command.expects == 1 && !satisfiable) {
            fail("expected SAT but solver returned UNSAT");
        }

        if (command.expects == 0 && satisfiable) {
            fail("expected UNSAT but solver returned SAT");
        }
    }

    private static int parseInt(String value, String name) {
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

    private static void usage() {
        System.err.println(
            "Usage: AlloyRunner "
                + "<model> <command-index> <solver> "
                + "<decompose-mode> <threads>"
        );
    }

    private static void fail(String message) {
        System.err.println("ERROR: " + message);
        System.exit(1);
    }
    }
