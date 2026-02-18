# Tab Structure

Date: 2026-02-18  
Status: Implemented

## Old Structure

Top-level tabs:
1. Executive View
2. Business Intelligence
3. Opportunity Ranking
4. Patent Details
5. Score Explainability
6. Export

Business Intelligence sub-tabs:
1. Rankings
2. Financial
3. Themes and Risk
4. Recommendations
5. Detailed View

## New Structure

Top-level tabs:
1. Overview
2. Portfolio Analysis
3. Patent Review
4. Reports and Export

Second-level tabs:
1. Overview -> Executive Summary
2. Portfolio Analysis -> Ranking, Financials, Themes and Risk
3. Patent Review -> Patent Details, Score Explainability, Recommendations
4. Reports and Export -> Business Report, Data Export

## Old -> New Mapping and Rationale

1. Executive View -> Overview / Executive Summary  
   Reason: keeps orientation metrics in a single entry point.

2. Business Intelligence / Rankings + Opportunity Ranking -> Portfolio Analysis / Ranking  
   Reason: removes duplicate ranking surfaces and creates one source of truth.

3. Business Intelligence / Financial -> Portfolio Analysis / Financials  
   Reason: financial analysis is a portfolio-level activity.

4. Business Intelligence / Themes and Risk -> Portfolio Analysis / Themes and Risk  
   Reason: theme segmentation and risk flags are part of portfolio screening.

5. Patent Details + Business Intelligence / Detailed View -> Patent Review / Patent Details  
   Reason: consolidates overlapping deep-dive views.

6. Score Explainability -> Patent Review / Score Explainability  
   Reason: explainability belongs with single-patent review and decision context.

7. Business Intelligence / Recommendations -> Patent Review / Recommendations  
   Reason: recommendations are patent-level actions.

8. Export + report download controls -> Reports and Export / Business Report + Data Export  
   Reason: all outbound artifacts now live in one destination.

## Rule Compliance

1. Journey-first grouping: yes (overview -> analysis -> review -> output).
2. Overlap removal: yes (duplicate ranking and detail surfaces merged).
3. Label clarity: yes (plain-English labels, consistent style).
4. Nesting depth: yes (maximum two levels).
