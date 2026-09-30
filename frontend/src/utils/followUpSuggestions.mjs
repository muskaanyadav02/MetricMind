
export function buildFollowUpSuggestions(result, question) {
  const normalizedQuestion = question.toLowerCase();

  const evidence = result?.evidence || {};
  const query = evidence.governed_query || {};

  const context = [
    normalizedQuestion,
    ...(Array.isArray(query.measures) ? query.measures : []),
    ...(Array.isArray(query.dimensions) ? query.dimensions : []),
    ...(Array.isArray(evidence.dimensions)
      ? evidence.dimensions
      : []),
  ]
    .filter((value) => typeof value === "string")
    .join(" ")
    .toLowerCase();

  let candidates;

  if (/profit|margin|loss/.test(context)) {
    candidates = [
      "Which category has the highest profit?",
      "Which region has the lowest profit?",
      "Show the yearly profit trend",
      "Which products have low profit?",
      "Which region has the highest sales?",
    ];
  } else if (/sales|revenue|turnover/.test(context)) {
    candidates = [
      "Which category has the highest sales?",
      "Which region has the highest sales?",
      "Show the monthly sales trend",
      "Which products generate the most profit?",
      "Compare sales across countries",
    ];
  } else if (/product|sub.?categor|category/.test(context)) {
    candidates = [
      "Which products have the highest profit?",
      "Which category has the highest sales?",
      "Which products have low profit?",
      "Which region has the highest sales?",
      "Show the yearly profit trend",
    ];
  } else if (/region|country|market/.test(context)) {
    candidates = [
      "Which region has the highest sales?",
      "Which category has the highest profit?",
      "Compare sales across countries",
      "Show the monthly sales trend",
      "Which products have low profit?",
    ];
  } else if (/month|year|date|trend|time/.test(context)) {
    candidates = [
      "Show the monthly sales trend",
      "Show the yearly profit trend",
      "Which category has the highest profit?",
      "Which region has the highest sales?",
      "Which products have low profit?",
    ];
  } else {
    candidates = [
      "Which category has the highest profit?",
      "Which region has the highest sales?",
      "Show the monthly sales trend",
      "Which products have low profit?",
      "Compare sales across countries",
    ];
  }

  const normalizedCurrentQuestion = question
    .trim()
    .toLowerCase()
    .replace(/[?!.\s]+$/, "");

  const uniqueSuggestions = [...new Set(candidates)].filter(
    (suggestion) =>
      suggestion
        .trim()
        .toLowerCase()
        .replace(/[?!.\s]+$/, "") !== normalizedCurrentQuestion
  );

  return uniqueSuggestions.slice(0, 3);
}
