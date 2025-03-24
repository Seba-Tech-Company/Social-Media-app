CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
	email VARCHAR(50) UNIQUE NOT NULL,
	phone TEXT[],
    password TEXT NOT NULL,  -- Store hashed passwords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE likes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    post_id TEXT NOT NULL,  -- MongoDB _id (string)
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extra_data JSONB DEFAULT '{}'  -- Store extra metadata like reactions
);

-- Add UNIQUE constraint separately
ALTER TABLE likes ADD CONSTRAINT unique_like UNIQUE (user_id, post_id);

-- Add Indexes for Performance
CREATE INDEX idx_likes_user ON likes(user_id);
CREATE INDEX idx_likes_post ON likes(post_id);

CREATE TABLE comment_likes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    comment_id TEXT NOT NULL,  -- MongoDB Comment _id
    liked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, comment_id)  -- Prevent duplicate likes
);


CREATE TABLE comments (
    comment_id SERIAL PRIMARY KEY,
    post_id TEXT NOT NULL,  -- Referencing MongoDB Post _id
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    parent_comment_id INT REFERENCES comments(comment_id) ON DELETE CASCADE,  -- For nested comments
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- Store likes, edits, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for performance
CREATE INDEX idx_comments_post ON comments(post_id);
CREATE INDEX idx_comments_user ON comments(user_id);
