
        // Theme toggle
        document.getElementById('theme-toggle').addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const isDark = document.body.classList.contains('dark-mode');
            document.cookie = `darkMode=${isDark}; path=/; max-age=${60 * 60 * 24 * 365}`;
        });

        // Leaderboard toggle
        const leaderboardToggle = document.getElementById('leaderboard-toggle');
        const leaderboardContent = document.getElementById('leaderboard-content');
        const leaderboardIcon = document.getElementById('leaderboard-icon');

        leaderboardToggle.addEventListener('click', function() {
            leaderboardContent.classList.toggle('open');
            leaderboardIcon.classList.toggle('open');
        });

        // Timer functionality
        let timeLeft = 30; // 30 seconds
        const timerBar = document.getElementById('timer-bar');
        const timerText = document.getElementById('timer-text');
        const timerContainer = document.getElementById('timer-container');

        // Set initial width
        timerBar.style.width = '100%';

        const interval = setInterval(() => {
            if (timeLeft <= 0) {
                clearInterval(interval);
                // Show time's up toast
                showToast("Time's up! Submitting your answer...", false);
                // Auto-submit after a short delay
                setTimeout(() => {
                    document.querySelector('.quiz-form').submit();
                }, 1500);
            } else {
                // Update timer text
                timerText.textContent = `${timeLeft} seconds remaining`;

                // Update progress bar width
                const percentage = (timeLeft / 30) * 100;
                timerBar.style.width = `${percentage}%`;

                // Add critical class when time is running low
                if (timeLeft <= 10) {
                    timerContainer.classList.add('timer-critical');

                    // Add pulse animation effect when time is critically low
                    if (timeLeft <= 5) {
                        timerText.classList.add('pulse');
                    }
                }

                timeLeft--;
            }
        }, 1000);

        // Form submission
        document.querySelector('.quiz-form').addEventListener('submit', function(e) {
            // Not preventing default as we want the form to submit to server
            // But we can show a toast notification
            showToast("Answer submitted successfully!", true);
        });

        // Toast notification function
        function showToast(message, isSuccess = true) {
            const toast = document.getElementById('toast');
            const toastMessage = document.getElementById('toast-message');
            const toastIcon = toast.querySelector('.toast-icon');

            // Set message and styling
            toastMessage.textContent = message;
            toast.className = `toast ${isSuccess ? 'toast-success show' : 'toast-error show'}`;
            toastIcon.className = `fas ${isSuccess ? 'fa-check-circle' : 'fa-exclamation-circle'} toast-icon`;

            // Hide after 3 seconds
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Add click animations to options
        const options = document.querySelectorAll('.option');
        options.forEach(option => {
            option.addEventListener('click', function() {
                // Remove active class from all options
                options.forEach(opt => opt.style.transform = '');

                // Add active class to clicked option
                this.style.transform = 'translateY(-2px)';
            });
        });

        // Show achievement popup if there's one to show
        {% if achievement %}
        setTimeout(() => {
            const popup = document.createElement('div');
            popup.className = 'achievement-popup show';
            popup.innerHTML = `
                <div class="achievement-icon">
                    <i class="fas fa-trophy"></i>
                </div>
                <div class="achievement-content">
                    <div class="achievement-title">Achievement Unlocked!</div>
                    <div class="achievement-desc">{{ achievement.name }}</div>
                </div>
            `;
            document.body.appendChild(popup);

            // Hide after 5 seconds
            setTimeout(() => {
                popup.classList.remove('show');
                setTimeout(() => popup.remove(), 500);
            }, 5000);
        }, 1000);
        {% endif %}
