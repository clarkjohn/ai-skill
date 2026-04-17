package com.clarkjohn.springdump;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

record CliOptions(
    Path repo,
    String profile,
    String configName,
    List<String> additionalLocations,
    boolean includeSystemEnvironment,
    boolean pretty,
    boolean help
) {
  static CliOptions parse(String[] args) {
    Path repo = Path.of(".");
    String profile = null;
    String configName = "application";
    List<String> additionalLocations = new ArrayList<>();
    boolean includeSystemEnvironment = false;
    boolean pretty = true;
    boolean help = false;

    for (int index = 0; index < args.length; index++) {
      String arg = args[index];
      switch (arg) {
        case "-h", "--help" -> help = true;
        case "--repo" -> repo = Path.of(requireValue(args, ++index, arg));
        case "--profile" -> profile = requireValue(args, ++index, arg);
        case "--config-name" -> configName = requireValue(args, ++index, arg);
        case "--config-location" -> additionalLocations.add(requireValue(args, ++index, arg));
        case "--include-system-environment" -> includeSystemEnvironment = true;
        case "--compact-json" -> pretty = false;
        default -> throw new IllegalArgumentException("Unknown argument: " + arg);
      }
    }

    return new CliOptions(
        repo.toAbsolutePath().normalize(),
        profile,
        configName,
        List.copyOf(additionalLocations),
        includeSystemEnvironment,
        pretty,
        help
    );
  }

  static String usage() {
    return """
        spring-config-dump

        Usage:
          java -jar spring-config-dump.jar --repo <path> [--profile prod] [options]

        Options:
          --repo <path>                     Target repo. Default: current directory.
          --profile <name>                 Active profile to resolve. Omit for base config.
          --config-name <name>             spring.config.name value. Default: application.
          --config-location <location>     Extra spring config location. Repeatable.
          --include-system-environment     Include current machine env/system properties.
          --compact-json                   Emit compact JSON.
          -h, --help                       Show help.
        """;
  }

  private static String requireValue(String[] args, int index, String flag) {
    if (index >= args.length) {
      throw new IllegalArgumentException("Missing value for " + flag);
    }
    return args[index];
  }
}
