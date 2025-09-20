class Hopper {
    constructor(ctx) {
        this.ctx = ctx;
        this.x = 200;
        this.y = 300;
        this.width = 40;
        this.height = 30;
        this.velocity = 0;
        this.gravity = 0.5;
        this.flapStrength = -8;
        this.color = 'gold';
    }

    flap() {
        this.velocity = this.flapStrength;
    }

    boost() {
        this.velocity = 10;
    }

    update() {
        this.velocity += this.gravity;
        this.y += this.velocity;
        
        // Boundary check
        if (this.y < 0) this.y = 0;
        if (this.y > 500 - this.height) this.y = 500 - this.height;
    }

    draw() {
        this.ctx.fillStyle = this.color;
        this.ctx.beginPath();
        this.ctx.ellipse(this.x, this.y, this.width/2, this.height/2, 0, 0, Math.PI*2);
        this.ctx.fill();
    }
}

class Game {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.hopper = new Hopper(this.ctx);
        this.score = 0;
        this.gameOver = false;
        this.animationId = null;
        
        // Event listeners
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') this.hopper.flap();
            if (e.code === 'ArrowDown') this.hopper.boost();
        });
        
        // Touch controls for mobile
        this.canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.hopper.flap();
        });
        
        // Swipe down for boost
        let startY;
        this.canvas.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
        }, {passive: false});
        
        this.canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const currentY = e.touches[0].clientY;
            if (currentY - startY > 50) {
                this.hopper.boost();
            }
        }, {passive: false});
    }

    start() {
        if (!this.animationId) {
            this.gameLoop();
        }
    }

    gameLoop() {
        this.update();
        this.draw();
        
        if (!this.gameOver) {
            this.animationId = requestAnimationFrame(() => this.gameLoop());
        }
    }

    update() {
        this.hopper.update();
        // Add obstacle logic here
        this.score += 0.1;
    }

    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw sky background
        this.ctx.fillStyle = 'skyblue';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw ground
        this.ctx.fillStyle = 'darkgreen';
        this.ctx.fillRect(0, 500, this.canvas.width, 100);
        
        // Draw hopper
        this.hopper.draw();
        
        // Draw score
        this.ctx.fillStyle = 'black';
        this.ctx.font = '24px Arial';
        this.ctx.fillText(`Score: ${Math.floor(this.score)}`, 20, 30);
    }
}

// Initialize game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const game = new Game('gameCanvas');
    document.getElementById('start-btn').addEventListener('click', () => {
        game.start();
    });
});