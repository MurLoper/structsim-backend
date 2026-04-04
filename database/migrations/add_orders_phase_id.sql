ALTER TABLE orders
  ADD COLUMN phase_id INT NULL COMMENT '项目阶段ID';

CREATE INDEX idx_orders_phase_id ON orders(phase_id);
