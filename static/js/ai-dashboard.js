/**
 * AI Dashboard - Admin interface for managing AI/ML components
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize charts and components if we're on the AI dashboard page
  const aiOverview = document.getElementById("ai-overview");
  if (!aiOverview) return;

  initializeCharts();
  initializeModelManagement();
});

/**
 * Initialize all charts on the AI dashboard
 */
function initializeCharts() {
  // AI Performance Chart
  const performanceCtx = document
    .getElementById("ai-performance-chart")
    .getContext("2d");
  new Chart(performanceCtx, {
    type: "line",
    data: {
      labels: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
      ],
      datasets: [
        {
          label: "Recommendation Accuracy",
          borderColor: "rgba(75, 192, 192, 1)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          data: [65, 67, 70, 71, 73, 75, 78, 79, 80, 81, 82, 84],
          tension: 0.3,
        },
        {
          label: "Prediction Accuracy",
          borderColor: "rgba(153, 102, 255, 1)",
          backgroundColor: "rgba(153, 102, 255, 0.2)",
          data: [60, 62, 64, 67, 68, 70, 72, 75, 76, 78, 80, 82],
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "AI System Performance Over Time",
        },
      },
      scales: {
        y: {
          beginAtZero: false,
          min: 50,
          max: 100,
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });

  // Model Accuracy Chart
  const accuracyCtx = document
    .getElementById("model-accuracy-chart")
    .getContext("2d");
  new Chart(accuracyCtx, {
    type: "radar",
    data: {
      labels: [
        "Performance Prediction",
        "Engagement Prediction",
        "Learning Style Detection",
        "Content Recommendation",
        "Knowledge Gap Detection",
      ],
      datasets: [
        {
          label: "Current Accuracy",
          data: [82, 78, 75, 85, 80],
          fill: true,
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgb(54, 162, 235)",
          pointBackgroundColor: "rgb(54, 162, 235)",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "rgb(54, 162, 235)",
        },
        {
          label: "Previous Month",
          data: [75, 72, 70, 81, 76],
          fill: true,
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderColor: "rgb(255, 99, 132)",
          pointBackgroundColor: "rgb(255, 99, 132)",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "rgb(255, 99, 132)",
        },
      ],
    },
    options: {
      elements: {
        line: {
          borderWidth: 3,
        },
      },
      scales: {
        r: {
          angleLines: {
            display: true,
          },
          suggestedMin: 50,
          suggestedMax: 100,
          ticks: {
            callback: function (value) {
              return value + "%";
            },
          },
        },
      },
    },
  });

  // Learning Style Distribution Chart
  if (document.getElementById("style-distribution-chart")) {
    const styleDistCtx = document
      .getElementById("style-distribution-chart")
      .getContext("2d");
    new Chart(styleDistCtx, {
      type: "doughnut",
      data: {
        labels: ["Visual", "Auditory", "Kinesthetic", "Reading/Writing"],
        datasets: [
          {
            data: [45, 23, 20, 12],
            backgroundColor: [
              "rgba(54, 162, 235, 0.8)",
              "rgba(255, 99, 132, 0.8)",
              "rgba(255, 206, 86, 0.8)",
              "rgba(75, 192, 192, 0.8)",
            ],
            borderColor: [
              "rgba(54, 162, 235, 1)",
              "rgba(255, 99, 132, 1)",
              "rgba(255, 206, 86, 1)",
              "rgba(75, 192, 192, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "right",
          },
          title: {
            display: true,
            text: "Learning Style Distribution",
          },
        },
      },
    });
  }

  // Recommendation Types Chart
  if (document.getElementById("recommendation-types-chart")) {
    const recTypesCtx = document
      .getElementById("recommendation-types-chart")
      .getContext("2d");
    new Chart(recTypesCtx, {
      type: "bar",
      data: {
        labels: [
          "Knowledge Gap",
          "Interest-Based",
          "Learning Path",
          "Similar Content",
          "Collaborative",
        ],
        datasets: [
          {
            label: "Number of Recommendations",
            data: [320, 280, 250, 220, 180],
            backgroundColor: [
              "rgba(255, 99, 132, 0.8)",
              "rgba(54, 162, 235, 0.8)",
              "rgba(255, 206, 86, 0.8)",
              "rgba(75, 192, 192, 0.8)",
              "rgba(153, 102, 255, 0.8)",
            ],
            borderColor: [
              "rgba(255, 99, 132, 1)",
              "rgba(54, 162, 235, 1)",
              "rgba(255, 206, 86, 1)",
              "rgba(75, 192, 192, 1)",
              "rgba(153, 102, 255, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  }

  // Recommendation Effectiveness Chart
  if (document.getElementById("recommendation-effectiveness-chart")) {
    const recEffCtx = document
      .getElementById("recommendation-effectiveness-chart")
      .getContext("2d");
    new Chart(recEffCtx, {
      type: "bar",
      data: {
        labels: [
          "Knowledge Gap",
          "Interest-Based",
          "Learning Path",
          "Similar Content",
          "Collaborative",
        ],
        datasets: [
          {
            label: "Engagement Rate",
            data: [75, 85, 70, 65, 60],
            backgroundColor: "rgba(54, 162, 235, 0.5)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
          {
            label: "Completion Rate",
            data: [65, 75, 60, 55, 50],
            backgroundColor: "rgba(255, 99, 132, 0.5)",
            borderColor: "rgba(255, 99, 132, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
  }

  // Performance Predictions Chart
  if (document.getElementById("performance-accuracy-chart")) {
    const perfAccCtx = document
      .getElementById("performance-accuracy-chart")
      .getContext("2d");
    new Chart(perfAccCtx, {
      type: "line",
      data: {
        labels: [
          "Week 1",
          "Week 2",
          "Week 3",
          "Week 4",
          "Week 5",
          "Week 6",
          "Week 7",
          "Week 8",
        ],
        datasets: [
          {
            label: "Predicted Performance",
            data: [72, 74, 75, 77, 78, 80, 82, 83],
            borderColor: "rgba(54, 162, 235, 1)",
            backgroundColor: "rgba(54, 162, 235, 0.1)",
            tension: 0.3,
            fill: false,
          },
          {
            label: "Actual Performance",
            data: [70, 72, 76, 75, 79, 81, 80, 84],
            borderColor: "rgba(255, 99, 132, 1)",
            backgroundColor: "rgba(255, 99, 132, 0.1)",
            tension: 0.3,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Predicted vs Actual Performance",
          },
          tooltip: {
            mode: "index",
            intersect: false,
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            min: 50,
            max: 100,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
  }

  // Disengagement Risk Distribution
  if (document.getElementById("disengagement-risk-chart")) {
    const disengageCtx = document
      .getElementById("disengagement-risk-chart")
      .getContext("2d");
    new Chart(disengageCtx, {
      type: "pie",
      data: {
        labels: ["Low Risk", "Medium Risk", "High Risk"],
        datasets: [
          {
            data: [65, 25, 10],
            backgroundColor: [
              "rgba(75, 192, 192, 0.8)",
              "rgba(255, 206, 86, 0.8)",
              "rgba(255, 99, 132, 0.8)",
            ],
            borderColor: [
              "rgba(75, 192, 192, 1)",
              "rgba(255, 206, 86, 1)",
              "rgba(255, 99, 132, 1)",
            ],
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "Student Disengagement Risk Distribution",
          },
        },
      },
    });
  }

  // Content by Learning Style Chart
  if (document.getElementById("content-by-style-chart")) {
    const contentStyleCtx = document
      .getElementById("content-by-style-chart")
      .getContext("2d");
    new Chart(contentStyleCtx, {
      type: "bar",
      data: {
        labels: [
          "Visual Content",
          "Auditory Content",
          "Interactive Content",
          "Text-Based Content",
        ],
        datasets: [
          {
            label: "Visual Learners",
            data: [85, 65, 75, 60],
            backgroundColor: "rgba(54, 162, 235, 0.7)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
          {
            label: "Auditory Learners",
            data: [65, 80, 70, 55],
            backgroundColor: "rgba(255, 99, 132, 0.7)",
            borderColor: "rgba(255, 99, 132, 1)",
            borderWidth: 1,
          },
          {
            label: "Kinesthetic Learners",
            data: [70, 65, 85, 60],
            backgroundColor: "rgba(255, 206, 86, 0.7)",
            borderColor: "rgba(255, 206, 86, 1)",
            borderWidth: 1,
          },
          {
            label: "Reading/Writing Learners",
            data: [60, 55, 65, 85],
            backgroundColor: "rgba(75, 192, 192, 0.7)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: "Content Effectiveness by Learning Style",
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: function (value) {
                return value + "%";
              },
            },
          },
        },
      },
    });
  }
}

/**
 * Initialize model management functionality
 */
function initializeModelManagement() {
  // Train model buttons
  const trainButtons = document.querySelectorAll(".train-model");
  const trainAllButton = document.getElementById("train-models-btn");
  const trainingModal = document.getElementById("training-modal");
  const closeModal = trainingModal.querySelector(".close-modal");
  const modelNameElement = document.getElementById("model-name");
  const trainingSamplesElement = document.getElementById("training-samples");
  const trainingStatusElement = document.getElementById("training-status");
  const progressBar = trainingModal.querySelector(".progress-value");
  const progressText = trainingModal.querySelector(".progress-text");
  const startTrainingButton = document.getElementById("start-training");
  const cancelTrainingButton = document.getElementById("cancel-training");

  let currentModel = "";

  // Open modal for individual model training
  trainButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const model = this.dataset.model;
      currentModel = model;

      // Set modal content
      modelNameElement.textContent = formatModelName(model);
      trainingSamplesElement.textContent = "Calculating...";
      trainingStatusElement.textContent = "Ready to train";
      progressBar.style.width = "0%";
      progressText.textContent = "Initializing...";

      // Show modal
      trainingModal.style.display = "block";

      // Get training data info
      fetchTrainingInfo(model);
    });
  });

  // Train all models
  if (trainAllButton) {
    trainAllButton.addEventListener("click", function () {
      currentModel = "all";

      // Set modal content
      modelNameElement.textContent = "All Models";
      trainingSamplesElement.textContent = "Calculating...";
      trainingStatusElement.textContent = "Ready to train";
      progressBar.style.width = "0%";
      progressText.textContent = "Initializing...";

      // Show modal
      trainingModal.style.display = "block";

      // Get training data info
      fetchTrainingInfo("all");
    });
  }

  // Close modal
  if (closeModal) {
    closeModal.addEventListener("click", function () {
      trainingModal.style.display = "none";
    });
  }

  // Start training
  if (startTrainingButton) {
    startTrainingButton.addEventListener("click", function () {
      startModelTraining(currentModel);
    });
  }

  // Cancel training
  if (cancelTrainingButton) {
    cancelTrainingButton.addEventListener("click", function () {
      trainingModal.style.display = "none";
    });
  }

  // View model details
  const viewModelButtons = document.querySelectorAll(".view-model");
  viewModelButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const model = this.dataset.model;
      alert(
        `Detailed view for ${formatModelName(model)} model would be shown here.`
      );
      // In a real implementation, this would show a modal with detailed model information
    });
  });
}

/**
 * Format a model name for display
 */
function formatModelName(modelKey) {
  switch (modelKey) {
    case "performance":
      return "Performance Prediction Model";
    case "engagement":
      return "Engagement Prediction Model";
    case "learning_style":
      return "Learning Style Detection Model";
    case "content_vectors":
      return "Content Recommendation Vectors";
    case "content_recommendation":
      return "Content Recommendation System";
    default:
      return modelKey
        .split("_")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
  }
}

/**
 * Fetch training information for a model
 */
function fetchTrainingInfo(model) {
  // In a real implementation, this would make an API call to get current training data statistics
  // Here we'll simulate it with random data

  setTimeout(() => {
    const trainingSamples = Math.floor(Math.random() * 500) + 200;
    document.getElementById("training-samples").textContent =
      trainingSamples.toString();
  }, 1000);
}

/**
 * Start training a model
 */
function startModelTraining(model) {
  const progressBar = document.querySelector(".training-modal .progress-value");
  const progressText = document.querySelector(".training-modal .progress-text");
  const trainingStatus = document.getElementById("training-status");
  const startButton = document.getElementById("start-training");
  const cancelButton = document.getElementById("cancel-training");

  // Disable buttons during training
  startButton.disabled = true;
  cancelButton.disabled = true;

  // Update status
  trainingStatus.textContent = "Training in progress...";

  // Create the payload for training
  const trainingData = {
    models: [model],
  };

  // Make the API call to train models
  fetch("/api/ai/train/models", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(trainingData),
  })
    .then((response) => {
      // Start progress animation (since the actual backend might be async)
      simulateTrainingProgress(
        progressBar,
        progressText,
        trainingStatus,
        startButton,
        cancelButton
      );
    })
    .catch((error) => {
      console.error("Error starting training:", error);
      trainingStatus.textContent = "Error: Failed to start training";
      startButton.disabled = false;
      cancelButton.disabled = false;
    });
}

/**
 * Simulate training progress animation
 */
function simulateTrainingProgress(
  progressBar,
  progressText,
  statusElement,
  startButton,
  cancelButton
) {
  let progress = 0;
  const interval = setInterval(() => {
    // Increment progress
    if (progress < 95) {
      // Simulate non-linear progress
      const increment = (95 - progress) / 10;
      progress += Math.min(increment, 10);
      progressBar.style.width = `${progress}%`;
      progressText.textContent = `${Math.round(progress)}% Complete`;

      // Update status messages at certain points
      if (progress > 20 && progress < 22) {
        statusElement.textContent = "Preparing training data...";
      } else if (progress > 40 && progress < 42) {
        statusElement.textContent = "Training model...";
      } else if (progress > 70 && progress < 72) {
        statusElement.textContent = "Evaluating model performance...";
      } else if (progress > 90) {
        statusElement.textContent = "Finalizing and saving model...";
      }
    } else {
      // Finish
      clearInterval(interval);
      progress = 100;
      progressBar.style.width = "100%";
      progressText.textContent = "100% Complete";
      statusElement.textContent = "Training complete!";

      // Re-enable buttons
      startButton.disabled = false;
      cancelButton.disabled = false;

      // Reload page after a delay to show updated model stats
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    }
  }, 300);
}
