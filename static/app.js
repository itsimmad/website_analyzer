// Chart.js chart instances
let uxChart, seoChart, performanceChart;

function createScoreChart(ctx, initialValue = 0, color = '#22c55e') {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [initialValue, 100 - initialValue],
                backgroundColor: [color, '#22223b'],
                borderWidth: 0,
                cutout: '75%',
            }],
        },
        options: {
            responsive: false,
            animation: {
                animateRotate: true,
                duration: 1200
            },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false },
            },
        },
    });
}

function getScoreColor(score) {
    if (score >= 80) return '#22c55e'; // Green
    if (score >= 50) return '#eab308'; // Yellow
    return '#ef4444'; // Red
}

function updateScoreChart(chart, score, color) {
    if (!chart) return;
    chart.data.datasets[0].data[0] = score;
    chart.data.datasets[0].data[1] = 100 - score;
    chart.data.datasets[0].backgroundColor[0] = color;
    chart.update();
}

// Initialize charts on DOMContentLoaded
function initScoreCharts() {
    if (!uxChart) {
        const uxCtx = document.getElementById('uxScoreChart').getContext('2d');
        uxChart = createScoreChart(uxCtx, 0, getScoreColor(0));
    }
    if (!seoChart) {
        const seoCtx = document.getElementById('seoScoreChart').getContext('2d');
        seoChart = createScoreChart(seoCtx, 0, getScoreColor(0));
    }
    if (!performanceChart) {
        const perfCtx = document.getElementById('performanceScoreChart').getContext('2d');
        performanceChart = createScoreChart(perfCtx, 0, getScoreColor(0));
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysisForm');
    const loadingAnimation = document.getElementById('loadingAnimation');
    const results = document.getElementById('results');
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === tabId) {
                    content.classList.add('active');
                }
            });
        });
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('url').value;
        const useAI = document.getElementById('useAI').checked;
        
        // Show loading animation
        loadingAnimation.classList.remove('hidden');
        results.classList.add('hidden');
        
        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, use_ai: useAI })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Hide loading animation and show results
            loadingAnimation.classList.add('hidden');
            results.classList.remove('hidden');
            
            // Check for errors
            if (data.error) {
                showError(data.error);
                return;
            }
            
            // Update scores and content
            updateScores(data);
            displayResults(data);
            
        } catch (error) {
            console.error('Error:', error);
            loadingAnimation.classList.add('hidden');
            showError('An error occurred while analyzing the website. Please try again.');
        }
    });

    initScoreCharts();

    function updateScores(data) {
        // UX
        const uxScore = data.ux_analysis.score || 0;
        const uxError = data.ux_analysis.error || '';
        updateScoreCircle('ux', uxScore, uxError);

        // SEO
        const seoScore = data.seo_analysis.score || 0;
        const seoError = data.seo_analysis.error || '';
        updateScoreCircle('seo', seoScore, seoError);

        // Performance
        const perfScore = data.performance_analysis.score || 0;
        const perfError = data.performance_analysis.error || '';
        updateScoreCircle('performance', perfScore, perfError);
    }

    function calculateScore(analysis) {
        if (analysis.error) {
            return 0;
        }
        
        // Simple scoring logic - can be enhanced based on your needs
        const totalMetrics = Object.keys(analysis).length;
        if (totalMetrics === 0) return 0;
        
        const positiveMetrics = Object.values(analysis).filter(value => 
            typeof value === 'boolean' ? value : 
            typeof value === 'string' && value.toLowerCase().includes('good')
        ).length;
        
        return Math.round((positiveMetrics / totalMetrics) * 100);
    }

    function updateScoreCircle(type, score, errorMsg) {
        let chart, scoreTextId;
        if (type === 'ux') {
            chart = uxChart;
            scoreTextId = 'uxScoreText';
        } else if (type === 'seo') {
            chart = seoChart;
            scoreTextId = 'seoScoreText';
        } else if (type === 'performance') {
            chart = performanceChart;
            scoreTextId = 'performanceScoreText';
        }
        const color = getScoreColor(score);
        updateScoreChart(chart, score, color);
        // Update score text
        const scoreText = document.getElementById(scoreTextId);
        if (scoreText) {
            scoreText.textContent = score + '%';
            scoreText.style.color = color;
        }
        // Show error message if present
        const errorElement = document.querySelector(`#${type} .score-error`);
        if (errorElement) {
            if (errorMsg) {
                errorElement.textContent = errorMsg;
                errorElement.style.display = 'block';
            } else {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
            }
        }
    }

    function displayResults(data) {
        // UX Analysis
        const uxContent = document.getElementById('uxContent');
        uxContent.innerHTML = createUXReport(data.ux_analysis);

        // SEO Analysis
        const seoContent = document.getElementById('seoContent');
        seoContent.innerHTML = createSEOReport(data.seo_analysis);

        // Performance Analysis
        const perfContent = document.getElementById('performanceContent');
        perfContent.innerHTML = createPerformanceReport(data.performance_analysis);
    }

    function createUXReport(ux) {
        if (ux.error) {
            return `<div class="analysis-card error"><h3 class="text-red-400">Error</h3><p class="text-gray-300">${ux.error}</p></div>`;
        }
        // Compose summary
        let summary = "The website performs well in overall usability.";
        if (ux.score < 80) summary = "The website has some usability issues that should be addressed.";
        if (ux.score < 50) summary = "The website has significant usability problems.";

        // Bullet points for each subsection
        const nav = ux.navigation;
        const read = ux.readability;
        const layout = ux.layout;
        const access = ux.accessibility;
        function statusIcon(val) {
            if (val === true) return '✅';
            if (val === false) return '❌';
            return '⚠️';
        }
        return `
            <div class="analysis-card">
                <div class="mb-2 text-lg font-bold text-blue-300">UX Score: <span class="text-white">${ux.score} / 100</span></div>
                <div class="mb-2 text-base text-gray-200">${summary}</div>
                <ul class="list-disc ml-6 space-y-1 text-gray-100">
                    <li><span class="font-semibold">Navigation:</span> ${Array.isArray(nav.broken_links) && nav.broken_links.length === 0 ? '✅ Clear and intuitive' : '⚠️ Some broken links detected'} (${nav.total_links || 0} links)</li>
                    <li><span class="font-semibold">Readability:</span> ${read.average_paragraph_length > 0 ? '✅ Good paragraph structure' : '⚠️ Needs more readable content'} (Avg. paragraph: ${read.average_paragraph_length || 0} words)</li>
                    <li><span class="font-semibold">Layout:</span> ${statusIcon(layout.has_header)} Header, ${statusIcon(layout.has_footer)} Footer, ${statusIcon(layout.has_main)} Main section</li>
                    <li><span class="font-semibold">Accessibility:</span> ${statusIcon(access.has_aria_labels)} ARIA labels, ${statusIcon(access.has_alt_text)} Alt text, ${statusIcon(access.has_skip_links)} Skip links</li>
                </ul>
                <div class="mt-4 p-3 bg-gray-800 rounded">
                    <div class="font-semibold text-blue-200 mb-1">Summary & Suggestions</div>
                    <ul class="list-disc ml-6 text-gray-200">
                        ${(nav.suggestions || []).concat(read.suggestions || [], layout.suggestions || [], access.suggestions || []).map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    function createSEOReport(seo) {
        if (seo.error) {
            return `<div class="analysis-card error"><h3 class="text-red-400">Error</h3><p class="text-gray-300">${seo.error}</p></div>`;
        }
        let summary = "The website is well-optimized for search engines.";
        if (seo.score < 80) summary = "Some SEO improvements are recommended.";
        if (seo.score < 50) summary = "The website has major SEO issues.";
        // Status helper
        function status(val) {
            if (val === true) return '<span class="text-green-400 font-bold">✅ Present</span>';
            if (val === false) return '<span class="text-red-400 font-bold">❌ Missing</span>';
            return '<span class="text-yellow-400 font-bold">⚠️ Incomplete</span>';
        }
        const meta = seo.meta_tags;
        const alt = seo.alt_tags;
        const headings = seo.headings;
        const mobile = seo.mobile_friendliness;
        const content = seo.content_analysis;
        return `
            <div class="analysis-card">
                <div class="mb-2 text-lg font-bold text-blue-300">SEO Score: <span class="text-white">${seo.score} / 100</span></div>
                <div class="mb-2 text-base text-gray-200">${summary}</div>
                <ul class="list-disc ml-6 space-y-1 text-gray-100">
                    <li><span class="font-semibold">Meta Title:</span> ${status(meta.has_title)}</li>
                    <li><span class="font-semibold">Meta Description:</span> ${status(meta.has_description)}</li>
                    <li><span class="font-semibold">Meta Keywords:</span> ${status(meta.has_keywords)}</li>
                    <li><span class="font-semibold">Alt Tags:</span> ${alt.total_images === 0 ? '<span class="text-yellow-400 font-bold">⚠️ No images</span>' : (alt.images_without_alt === 0 ? '<span class="text-green-400 font-bold">✅ All images have alt</span>' : '<span class="text-red-400 font-bold">❌ Missing alt text</span>')}</li>
                    <li><span class="font-semibold">Headings:</span> ${headings.total_headings > 0 ? '<span class="text-green-400 font-bold">✅ Present</span>' : '<span class="text-red-400 font-bold">❌ Missing</span>'} (H1: ${headings.h1_count})</li>
                    <li><span class="font-semibold">Mobile Friendly:</span> ${status(mobile.has_viewport)}</li>
                    <li><span class="font-semibold">Content:</span> ${content.total_words > 0 ? '<span class="text-green-400 font-bold">✅ Sufficient</span>' : '<span class="text-red-400 font-bold">❌ Insufficient</span>'} (${content.total_words} words)</li>
                </ul>
                <div class="mt-4 p-3 bg-gray-800 rounded">
                    <div class="font-semibold text-blue-200 mb-1">Summary & Suggestions</div>
                    <ul class="list-disc ml-6 text-gray-200">
                        ${(meta.suggestions || []).concat(alt.suggestions || [], headings.suggestions || [], mobile.suggestions || [], content.suggestions || []).map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    function createPerformanceReport(perf) {
        if (perf.error) {
            return `<div class="analysis-card error"><h3 class="text-red-400">Error</h3><p class="text-gray-300">${perf.error}</p></div>`;
        }
        let summary = "The website loads quickly and is well-optimized.";
        if (perf.score < 80) summary = "Some performance optimizations are recommended.";
        if (perf.score < 50) summary = "The website has major performance issues.";
        return `
            <div class="analysis-card">
                <div class="mb-2 text-lg font-bold text-blue-300">Performance Score: <span class="text-white">${perf.score} / 100</span></div>
                <div class="mb-2 text-base text-gray-200">${summary}</div>
                <ul class="list-disc ml-6 space-y-1 text-gray-100">
                    <li><span class="font-semibold">Load Time:</span> ${perf.load_time}</li>
                    <li><span class="font-semibold">Page Size:</span> ${perf.page_size}</li>
                    <li><span class="font-semibold">Resources:</span> ${perf.resource_count.scripts} scripts, ${perf.resource_count.stylesheets} stylesheets, ${perf.resource_count.images} images</li>
                    <li><span class="font-semibold">Compression:</span> ${perf.optimization_features.compression_enabled ? '✅ Enabled' : '❌ Not enabled'}</li>
                    <li><span class="font-semibold">Caching:</span> ${perf.optimization_features.caching_enabled ? '✅ Enabled' : '❌ Not enabled'}</li>
                </ul>
                <div class="mt-4 p-3 bg-gray-800 rounded">
                    <div class="font-semibold text-blue-200 mb-1">Suggestions</div>
                    <ul class="list-disc ml-6 text-gray-200">
                        ${(perf.suggestions || []).map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        form.insertAdjacentElement('beforebegin', errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}); 