package com.clarkjohn.springdump;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.boot.DefaultBootstrapContext;
import org.springframework.boot.SpringBootVersion;
import org.springframework.boot.context.config.ConfigDataEnvironmentPostProcessor;
import org.springframework.boot.origin.Origin;
import org.springframework.boot.origin.OriginLookup;
import org.springframework.core.env.ConfigurableEnvironment;
import org.springframework.core.env.EnumerablePropertySource;
import org.springframework.core.env.MapPropertySource;
import org.springframework.core.env.MutablePropertySources;
import org.springframework.core.env.PropertySource;
import org.springframework.core.env.StandardEnvironment;
import org.springframework.core.io.DefaultResourceLoader;

final class SpringConfigDumpService {
  private static final String CLI_SOURCE = "spring-config-dump-cli";
  private static final Set<String> INTERNAL_KEYS = Set.of(
      "spring.config.additional-location",
      "spring.config.location",
      "spring.config.name",
      "spring.main.web-application-type",
      ConfigDataEnvironmentPostProcessor.ON_LOCATION_NOT_FOUND_PROPERTY
  );
  private static final List<String> INTERNAL_PREFIXES = List.of(
      "spring.config.activate.",
      "spring.profiles."
  );

  ConfigDump dump(CliOptions options) {
    ConfigurableEnvironment environment = new StandardEnvironment();
    if (!options.includeSystemEnvironment()) {
      stripAmbientSources(environment.getPropertySources());
    }

    environment.getPropertySources().addFirst(new MapPropertySource(CLI_SOURCE, cliDefaults(options)));

    Collection<String> additionalProfiles = options.profile() == null
        ? List.of()
        : List.of(options.profile());

    ConfigDataEnvironmentPostProcessor.applyTo(
        environment,
        new DefaultResourceLoader(),
        new DefaultBootstrapContext(),
        additionalProfiles
    );

    return toDump(environment, options.profile());
  }

  private ConfigDump toDump(ConfigurableEnvironment environment, String profile) {
    List<EnumerablePropertySource<?>> enumerableSources = new ArrayList<>();
    for (PropertySource<?> source : environment.getPropertySources()) {
      if (!(source instanceof EnumerablePropertySource<?> enumerable)) {
        continue;
      }
      if (!includePropertySource(enumerable)) {
        continue;
      }
      enumerableSources.add(enumerable);
    }

    Map<String, EffectiveProperty> effective = new LinkedHashMap<>();
    Map<String, List<PropertyLayer>> layers = new LinkedHashMap<>();

    List<EnumerablePropertySource<?>> reversed = new ArrayList<>(enumerableSources);
    Collections.reverse(reversed);

    for (EnumerablePropertySource<?> source : reversed) {
      for (String name : sortedPropertyNames(source)) {
        if (isInternalKey(name)) {
          continue;
        }

        Object value = source.getProperty(name);
        if (value == null) {
          continue;
        }

        String stringValue = String.valueOf(value);
        String origin = originOf(source, name);
        layers.computeIfAbsent(name, ignored -> new ArrayList<>())
            .add(new PropertyLayer(stringValue, source.getName(), origin));
        effective.put(name, new EffectiveProperty(stringValue, source.getName(), origin));
      }
    }

    return new ConfigDump(
        SpringBootVersion.getVersion(),
        profile,
        enumerableSources.stream().map(PropertySource::getName).toList(),
        effective,
        layers
    );
  }

  private boolean includePropertySource(EnumerablePropertySource<?> source) {
    String name = source.getName();
    if (CLI_SOURCE.equals(name)) {
      return false;
    }
    return name.contains("Config resource")
        || name.contains("applicationConfig")
        || name.contains("Config tree")
        || name.contains("systemEnvironment")
        || name.contains("systemProperties");
  }

  private List<String> sortedPropertyNames(EnumerablePropertySource<?> source) {
    return Set.of(source.getPropertyNames()).stream().sorted().toList();
  }

  @SuppressWarnings({"rawtypes", "unchecked"})
  private String originOf(EnumerablePropertySource<?> source, String name) {
    if (source instanceof OriginLookup lookup) {
      Origin origin = (Origin) lookup.getOrigin(name);
      return origin != null ? origin.toString() : null;
    }
    return null;
  }

  private Map<String, Object> cliDefaults(CliOptions options) {
    List<String> locations = new ArrayList<>();
    Path repo = options.repo();
    locations.add("optional:file:" + repo + "/");
    locations.add("optional:file:" + repo + "/config/");
    locations.add("optional:file:" + repo + "/src/main/resources/");
    locations.addAll(options.additionalLocations());

    return Map.of(
        "spring.config.name", options.configName(),
        "spring.config.additional-location", locations.stream().collect(Collectors.joining(",")),
        "spring.main.web-application-type", "none",
        ConfigDataEnvironmentPostProcessor.ON_LOCATION_NOT_FOUND_PROPERTY, "ignore"
    );
  }

  private void stripAmbientSources(MutablePropertySources sources) {
    sources.remove(StandardEnvironment.SYSTEM_ENVIRONMENT_PROPERTY_SOURCE_NAME);
    sources.remove(StandardEnvironment.SYSTEM_PROPERTIES_PROPERTY_SOURCE_NAME);
  }

  private boolean isInternalKey(String name) {
    if (INTERNAL_KEYS.contains(name)) {
      return true;
    }
    return INTERNAL_PREFIXES.stream().anyMatch(name::startsWith);
  }
}
