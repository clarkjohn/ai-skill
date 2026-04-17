package com.clarkjohn.springdump;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

public final class SpringConfigDumpApplication {
  private SpringConfigDumpApplication() {}

  public static void main(String[] args) throws Exception {
    CliOptions options;
    try {
      options = CliOptions.parse(args);
    } catch (IllegalArgumentException error) {
      System.err.println(error.getMessage());
      System.err.println();
      System.err.println(CliOptions.usage());
      System.exit(2);
      return;
    }

    if (options.help()) {
      System.out.println(CliOptions.usage());
      return;
    }

    ConfigDump dump = new SpringConfigDumpService().dump(options);
    ObjectMapper mapper = new ObjectMapper();
    if (options.pretty()) {
      mapper.enable(SerializationFeature.INDENT_OUTPUT);
    }
    System.out.println(mapper.writeValueAsString(dump));
  }
}
