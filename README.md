# sciencemadevisual-website
Science Made Visual website — pharmacology &amp; healthcare leadership explainers

## Adding a shop product

The Shop grid on the home page and the shop in the SMV Pharmacology app read the same feed,
`shop/products.json`, live at https://www.sciencemadevisual.co.uk/shop/products.json. Adding a new Etsy listing to
the feed updates both. From this folder, run one command:

```bash
python3 scripts/add_shop_product.py \
  --title "Tablet Transporter: Giant Tablet 7-Day Trinket Box" \
  --price "£19.99" \
  --url "https://www.etsy.com/uk/listing/4618693468" \
  --photo "/path/to/a/real/photo.jpg" \
  --push
```

- Use a real photo of the product. If a square crop sits beside it (`square/<name>_1x1.jpg`, as in the Model Sites
  photo folders), the script uses that instead.
- The script saves a square 800 px JPEG with no EXIF or GPS at `images/shop/<id>.jpg` (under about 150 KB), puts the
  product at the top of the feed with today's date, updates `updated`, and refuses a listing that is already there.
- `--id slug` sets the id. Without it, the id comes from the title before any colon (`tablet-transporter`).
- `--dry-run` shows what would happen and writes nothing.
- `--push` brings `main` up to date, commits the feed and the photo on `main`, and pushes, so the site and the app
  pick it up within a couple of minutes. Leave it off to look first; the script then prints the git commands.
- Needs only Python 3 and macOS (it uses `sips` for the photo). No venv or extra packages.

The feed's shape is a contract with the app, so keep it exactly like this (newest first, `image` always an absolute
https URL):

```json
{"updated": "YYYY-MM-DD", "products": [
  {"id": "tablet-transporter", "title": "...", "price": "£19.99",
   "url": "https://www.etsy.com/uk/listing/...",
   "image": "https://www.sciencemadevisual.co.uk/images/shop/tablet-transporter.jpg", "added": "YYYY-MM-DD"}
]}
```

To change or remove a product, edit `shop/products.json` by hand, check it is still valid JSON
(`python3 -m json.tool shop/products.json`), and push. If the feed ever fails to load, the site hides the grid and
keeps the "Visit the Lunchbox Designs Etsy shop" button.
