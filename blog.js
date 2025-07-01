const blogContainer = document.getElementById('blog-container');
const tagFilter = document.getElementById('tagFilter');
const sortOrder = document.getElementById('sortOrder');

let posts = [];

fetch('/blog/posts.json')
  .then(res => res.json())
  .then(data => {
    posts = data;
    initFilters();
    renderPosts();
  });

function initFilters() {
  const tags = new Set();
  posts.forEach(post => post.tags?.forEach(tag => tags.add(tag)));
  tags.forEach(tag => {
    const option = document.createElement('option');
    option.value = tag;
    option.textContent = tag;
    tagFilter.appendChild(option);
  });

  tagFilter.addEventListener('change', renderPosts);
  sortOrder.addEventListener('change', renderPosts);
}

function renderPosts() {
  const tag = tagFilter.value;
  const order = sortOrder.value;

  let filtered = [...posts];
  if (tag !== 'all') {
    filtered = filtered.filter(p => p.tags.includes(tag));
  }

  filtered.sort((a, b) => order === 'desc'
    ? new Date(b.date) - new Date(a.date)
    : new Date(a.date) - new Date(b.date)
  );

  blogContainer.innerHTML = '';
  if (!filtered.length) {
    blogContainer.innerHTML = '<p>No posts found.</p>';
    return;
  }

  filtered.forEach(post => {
    fetch(`/blog/posts/${post.file}`)
      .then(res => res.text())
      .then(text => {
        const parsed = matter(text);
        const html = marked.parse(parsed.content);
        const div = document.createElement('section');
        div.className = 'blog-post';
        div.innerHTML = `
          <h2>${parsed.data.title}</h2>
          <p><em>${new Date(parsed.data.date).toLocaleDateString()} | Tags: ${parsed.data.tags.join(', ')}</em></p>
          ${html}
        `;
        blogContainer.appendChild(div);
      });
  });
}
