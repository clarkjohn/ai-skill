package com.clarkjohn.springdump;

import java.util.List;
import java.util.Map;

record ConfigDump(
    String bootVersion,
    String profile,
    List<String> appliedPropertySources,
    Map<String, EffectiveProperty> effectiveProperties,
    Map<String, List<PropertyLayer>> layers
) {}

record EffectiveProperty(
    String value,
    String propertySource,
    String origin
) {}

record PropertyLayer(
    String value,
    String propertySource,
    String origin
) {}
