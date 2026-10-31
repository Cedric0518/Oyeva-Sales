/** A File with a given name and size, without allocating the bytes. */
export function makeFile(name: string, size = 1024, type = ''): File {
  const file = new File(['x'], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
}
