// Daily tracking AJAX logic for user dashboard
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("tracking-form");
    if (!form) {
        // Not on user dashboard, nothing to do
        return;
    }

    const waterCb = document.getElementById("water_completed");
    const foodCb = document.getElementById("food_completed");
    const workoutCb = document.getElementById("workout_completed");
    const challengeCb = document.getElementById("challenge_completed");
    const progressBar = document.getElementById("progress-bar");
    const trackingMessage = document.getElementById("tracking-message");

    function sendUpdate() {
        const payload = {
            water_completed: waterCb.checked,
            food_completed: foodCb.checked,
            workout_completed: workoutCb.checked,
            challenge_completed: challengeCb.checked
        };

        fetch("/user/daily-tracking", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
            .then(resp => resp.json())
            .then(data => {
                if (data && data.success) {
                    const progress = data.progress;
                    progressBar.style.width = progress + "%";
                    progressBar.textContent = progress + "%";
                    trackingMessage.textContent = data.message;
                }
            })
            .catch(err => {
                console.error("Tracking update failed", err);
            });
    }

    [waterCb, foodCb, workoutCb, challengeCb].forEach(cb => {
        if (cb) {
            cb.addEventListener("change", sendUpdate);
        }
    });
});

