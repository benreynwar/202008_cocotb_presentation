library ieee;
use ieee.numeric_std.all;

entity adder is
  port (
    a_data: in unsigned(2 downto 0);
    b_data: in unsigned(2 downto 0);
    c_data: out unsigned(3 downto 0)
    );
end entity;

architecture arch of adder is
begin
  c_data <= resize(a_data, 4) + resize(b_data, 4);
end architecture;
