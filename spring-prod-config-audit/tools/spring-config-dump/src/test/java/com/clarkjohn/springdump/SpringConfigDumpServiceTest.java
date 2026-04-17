package com.clarkjohn.springdump;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

class SpringConfigDumpServiceTest {
  @Test
  void loadsProfileOverridesAndOrigins() throws IOException {
    Path repo = Files.createTempDirectory("spring-config-dump-test");
    Files.createDirectories(repo.resolve("src/main/resources"));
    Files.writeString(
        repo.resolve("src/main/resources/application.yml"),
        """
        service:
          endpoint: https://base.example
          timeout: 10
        ---
        spring:
          config:
            activate:
              on-profile: prod
        service:
          endpoint: https://prod.example
        """
    );

    CliOptions options = new CliOptions(repo, "prod", "application", List.of(), false, true, false);
    ConfigDump dump = new SpringConfigDumpService().dump(options);

    assertThat(dump.bootVersion()).startsWith("3.5.");
    assertThat(dump.effectiveProperties()).containsKey("service.endpoint");
    assertThat(dump.effectiveProperties().get("service.endpoint").value()).isEqualTo("https://prod.example");
    assertThat(dump.layers().get("service.endpoint")).hasSize(2);
    assertThat(dump.layers().get("service.endpoint").get(0).value()).isEqualTo("https://base.example");
    assertThat(dump.layers().get("service.endpoint").get(1).value()).isEqualTo("https://prod.example");
    assertThat(dump.effectiveProperties().get("service.timeout").value()).isEqualTo("10");
    assertThat(dump.effectiveProperties()).doesNotContainKey("spring.config.activate.on-profile");
  }
}
