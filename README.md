# podem_atpg

## A From-Scratch Implementation of the PODEM Algorithm for Automatic Test Pattern Generation (ATPG)

**Author:** Jonah O'Brien Weiss  
**Date:** May 11, 2022

This repository contains a pure implementation of the PODEM (Path-Oriented Decision Making) algorithm for Automatic Test Pattern Generation, developed from scratch without relying on any external libraries or frameworks.

## About ATPG

Automatic Test Pattern Generation (ATPG) is an electronic design automation method used to find input sequences that can distinguish between correct circuit behavior and faulty circuit behavior caused by defects. The generated patterns are used to test semiconductor devices after manufacture or to assist with failure analysis. ATPG effectiveness is measured by the number of modeled defects detectable and the number of generated patterns, which indicate test quality and test application time.

## The PODEM Algorithm

PODEM (Path-Oriented Decision Making) is an improvement over the D Algorithm for ATPG. It was created in 1981 by Prabhu Goel to address the limitations of the D Algorithm when dealing with complex circuit designs. PODEM is particularly effective because it:

- Uses a systematic approach to propagate fault effects to primary outputs
- Makes decisions based on path sensitization
- Handles complex circuit structures more efficiently than earlier algorithms
- Provides a robust framework for generating test patterns for stuck-at faults

For more information about ATPG and its algorithmic methods, visit the [Wikipedia article on Automatic Test Pattern Generation](https://en.wikipedia.org/wiki/Automatic_test_pattern_generation#Algorithmic_methods).
