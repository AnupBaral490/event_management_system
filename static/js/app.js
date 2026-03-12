document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.feature-card, .event-card, .glass-card, .stat-card');
  cards.forEach((card, index) => {
    card.classList.add('reveal');
    card.style.animationDelay = `${index * 0.06}s`;
  });
});
