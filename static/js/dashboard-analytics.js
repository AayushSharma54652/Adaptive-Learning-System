/**
 * Dashboard Analytics - Provides ML/AI-powered visualizations for the student dashboard
 */

document.addEventListener("DOMContentLoaded", function () {
  // Check if we're on the dashboard page
  const dashboardContainer = document.querySelector(".dashboard-container");
  if (!dashboardContainer) return;

  // Initialize analytics components
  initPerformancePrediction();
  initLearningStyleViz();
  initEngagementTracking();
});

/**
 * Initialize the performance prediction visualization
 */
function initPerformancePrediction() {
  // Create container if it doesn't exist
  let container = document.getElementById("performance-prediction");
  if (!container) {
    // Find progress section
    const progressSection = document.querySelector(
      ".dashboard-section.progress-section"
    );
    if (!progressSection) return;

    // Create prediction container
    container = document.createElement("div");
    container.id = "performance-prediction";
    container.className = "prediction-container";
    container.innerHTML = `
            <h4>AI Performance Prediction</h4>
            <div class="prediction-content">
                <div class="prediction-loading">Loading AI prediction...</div>
            </div>
        `;

    // Add to DOM
    progressSection.appendChild(container);
  }

  // Fetch prediction data
  fetch("/api/ai/predict/performance")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        container.querySelector(".prediction-content").innerHTML = `
                    <div class="prediction-error">
                        <p>Not enough data to make a prediction yet.</p>
                        <p>Continue learning to get AI-powered insights!</p>
                    </div>
                `;
        return;
      }

      // Calculate prediction level class
      let levelClass = "average";
      if (data.predicted_performance > 0.8) levelClass = "excellent";
      else if (data.predicted_performance > 0.6) levelClass = "good";
      else if (data.predicted_performance < 0.4)
        levelClass = "needs-improvement";

      // Format the prediction value
      const predictionPercent = Math.round(data.predicted_performance * 100);

      // Update content
      container.querySelector(".prediction-content").innerHTML = `
                <div class="prediction-score ${levelClass}">
                    <div class="score-circle">
                        <span class="score-value">${predictionPercent}%</span>
                    </div>
                    <div class="score-label">Predicted Performance</div>
                </div>
                <div class="prediction-message">
                    <p>Our AI predicts your future assessment performance based on your learning patterns.</p>
                    <p class="prediction-action">
                        ${getActionMessage(predictionPercent)}
                    </p>
                </div>
            `;
    })
    .catch((error) => {
      console.error("Error fetching prediction:", error);
      container.querySelector(".prediction-content").innerHTML = `
                <div class="prediction-error">
                    <p>Unable to load prediction at this time.</p>
                </div>
            `;
    });
}

/**
 * Get action message based on prediction score
 */
function getActionMessage(score) {
  if (score >= 85) {
    return "You're on track for excellent results! Consider exploring more advanced content.";
  } else if (score >= 70) {
    return "You're doing well! Focus on your recommended content to maintain progress.";
  } else if (score >= 50) {
    return "You're making progress. Spending more time with practice exercises could help boost your performance.";
  } else {
    return "You might benefit from revisiting fundamental concepts. Check out your recommended remedial content.";
  }
}

/**
 * Initialize the learning style visualization
 */
function initLearningStyleViz() {
  // Create container if it doesn't exist
  let container = document.getElementById("learning-style-viz");
  if (!container) {
    // Find learning path section
    const learningSection = document.querySelector(
      ".dashboard-section.learning-path-section"
    );
    if (!learningSection) return;

    // Create container
    container = document.createElement("div");
    container.id = "learning-style-viz";
    container.className = "learning-style-container";
    container.innerHTML = `
            <h4>Your Learning Style Profile</h4>
            <div class="learning-style-content">
                <div class="learning-style-loading">Analyzing your learning patterns...</div>
            </div>
        `;

    // Add to DOM
    learningSection.appendChild(container);
  }

  // Fetch learning style data
  fetch("/api/ai/user/learning-style")
    .then((response) => response.json())
    .then((data) => {
      if (!data.enough_data) {
        container.querySelector(".learning-style-content").innerHTML = `
                    <div class="style-not-enough-data">
                        <p>We're still learning about your learning style preferences.</p>
                        <p>Continue interacting with different types of content for better personalization.</p>
                    </div>
                `;
        return;
      }

      // Fetch visualization
      return fetch("/api/ai/user/learning-style/visualization")
        .then((response) => response.json())
        .then((vizData) => {
          // Update content
          container.querySelector(".learning-style-content").innerHTML = `
                        <div class="style-info">
                            <h5>${capitalizeFirstLetter(
                              data.style
                            )} Learner</h5>
                            <p>${data.description}</p>
                        </div>
                        <div class="style-visualization">
                            <img src="${
                              vizData.visualization
                            }" alt="Learning Style Visualization">
                        </div>
                        <div class="style-tips">
                            <h5>Personalization Tips</h5>
                            <p>Based on your learning style, we'll emphasize ${getStyleEmphasis(
                              data.style
                            )} in your learning materials.</p>
                        </div>
                    `;
        });
    })
    .catch((error) => {
      console.error("Error fetching learning style:", error);
      container.querySelector(".learning-style-content").innerHTML = `
                <div class="style-error">
                    <p>Unable to analyze learning style at this time.</p>
                </div>
            `;
    });
}

/**
 * Get description of what will be emphasized based on learning style
 */
function getStyleEmphasis(style) {
  switch (style) {
    case "visual":
      return "diagrams, videos, and visual representations";
    case "auditory":
      return "discussions, audio elements, and verbal explanations";
    case "kinesthetic":
      return "interactive exercises, hands-on activities, and practical applications";
    case "reading/writing":
      return "comprehensive text materials, note-taking opportunities, and written exercises";
    default:
      return "a balanced mix of different content types";
  }
}

/**
 * Initialize the engagement tracking component
 */
function initEngagementTracking() {
  // Create container if it doesn't exist
  let container = document.getElementById("engagement-tracking");
  if (!container) {
    // Find recommendations section
    const recsSection = document.querySelector(
      ".dashboard-section.recommendations-section"
    );
    if (!recsSection) return;

    // Create container
    container = document.createElement("div");
    container.id = "engagement-tracking";
    container.className = "engagement-container";
    container.innerHTML = `
            <h4>Learning Engagement Insights</h4>
            <div class="engagement-content">
                <div class="engagement-loading">Analyzing your engagement patterns...</div>
            </div>
        `;

    // Add to DOM
    recsSection.insertBefore(container, recsSection.firstChild.nextSibling);
  }

  // Fetch engagement data
  fetch("/api/ai/predict/disengagement")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        container.querySelector(".engagement-content").innerHTML = `
            <div class="engagement-error">
                <p>Not enough data to analyze engagement patterns yet.</p>
            </div>
        `;
        return;
      }

      // Create engagement status indicator
      let statusClass = "status-good";
      let statusMessage = "Excellent engagement";

      if (data.risk_level === "high") {
        statusClass = "status-danger";
        statusMessage = "At risk of disengagement";
      } else if (data.risk_level === "medium") {
        statusClass = "status-warning";
        statusMessage = "Moderate engagement";
      }

      // Create HTML for contributing factors
      let factorsHtml = "";
      if (data.contributing_factors && data.contributing_factors.length > 0) {
        factorsHtml = `
            <div class="factors-list">
                <h5>Suggestions for Improvement</h5>
                <ul>
                    ${data.contributing_factors
                      .map(
                        (factor) =>
                          `<li><strong>${factor.factor}:</strong> ${factor.description}</li>`
                      )
                      .join("")}
                </ul>
            </div>
        `;
      }

      // Update content
      container.querySelector(".engagement-content").innerHTML = `
        <div class="engagement-status ${statusClass}">
            <div class="status-indicator"></div>
            <div class="status-message">${statusMessage}</div>
        </div>
        <div class="engagement-details">
            <p>Your engagement pattern is tracked by our AI to help personalize your learning journey.</p>
            ${factorsHtml}
        </div>
    `;
    })
    .catch((error) => {
      console.error("Error fetching engagement data:", error);
      container.querySelector(".engagement-content").innerHTML = `
        <div class="engagement-error">
            <p>Unable to analyze engagement at this time.</p>
        </div>
    `;
    });
}

/**
 * Helper function to capitalize first letter of a string
 */
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}
