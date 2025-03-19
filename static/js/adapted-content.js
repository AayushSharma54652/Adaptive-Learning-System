// Adapted Content JavaScript - For enhanced display of adapted learning content

document.addEventListener('DOMContentLoaded', function() {
    // Check if this is adapted content
    const contentContainer = document.querySelector('.learning-container');
    const isAdapted = contentContainer && contentContainer.dataset.isAdapted === 'true';
    
    if (isAdapted) {
        // Add a special class to the container
        contentContainer.classList.add('adapted-content');
        
        // Add an adaptation notification banner
        const adaptationBanner = document.createElement('div');
        adaptationBanner.className = 'adaptation-banner';
        
        const bannerContent = document.createElement('div');
        bannerContent.className = 'banner-content';
        
        const bannerIcon = document.createElement('div');
        bannerIcon.className = 'banner-icon';
        bannerIcon.innerHTML = '<i class="icon-info"></i>';
        
        const bannerText = document.createElement('div');
        bannerText.className = 'banner-text';
        bannerText.innerHTML = `
            <h4>Personalized Learning Content</h4>
            <p>This content has been adapted based on your assessment results to help you better understand the concepts.</p>
        `;
        
        bannerContent.appendChild(bannerIcon);
        bannerContent.appendChild(bannerText);
        adaptationBanner.appendChild(bannerContent);
        
        // Insert the banner at the top of the content
        const contentHeader = document.querySelector('.learning-header');
        contentContainer.insertBefore(adaptationBanner, contentHeader.nextSibling);
        
        // Highlight sections that have been simplified
        const simplifiedSections = document.querySelectorAll('.content-section h3[data-simplified="true"]');
        simplifiedSections.forEach(section => {
            section.classList.add('simplified-section-title');
            section.parentElement.classList.add('simplified-section');
            
            // Add a helper icon
            const helperIcon = document.createElement('span');
            helperIcon.className = 'simplified-icon';
            helperIcon.innerHTML = '<i class="icon-help"></i>';
            helperIcon.title = 'This section has been simplified to help your understanding';
            section.appendChild(helperIcon);
        });
        
        // Add click handlers for practice exercises
        const practiceExercises = document.querySelectorAll('.practice-exercise');
        practiceExercises.forEach(exercise => {
            const answerButton = exercise.querySelector('.show-answer');
            const answer = exercise.querySelector('.exercise-answer');
            
            if (answerButton && answer) {
                answer.style.display = 'none';
                
                answerButton.addEventListener('click', function() {
                    if (answer.style.display === 'none') {
                        answer.style.display = 'block';
                        answerButton.textContent = 'Hide Answer';
                    } else {
                        answer.style.display = 'none';
                        answerButton.textContent = 'Show Answer';
                    }
                });
            }
        });
        
        // Log that the student is viewing adapted content
        logAdaptedContentView();
    }
    
    function logAdaptedContentView() {
        // Get content ID from URL or data attribute
        const contentId = window.location.pathname.split('/').pop() || 
                        contentContainer.dataset.contentId;
        
        // Log the interaction
        fetch('/api/log-interaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                content_id: contentId,
                type: 'view_adapted_content',
                timestamp: new Date().toISOString(),
                details: {
                    is_adapted: true
                }
            })
        }).catch(error => console.error('Error logging interaction:', error));
    }
});