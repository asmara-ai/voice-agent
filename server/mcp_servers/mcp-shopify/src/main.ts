import { ShopifyClient } from "./ShopifyClient/ShopifyClient.js";
// fetch("https://miraiminds.myshopify.com/admin/api/2025-04/graphql.json", {
//   method: "POST",
//   headers: {
//     "Content-Type": "application/json",
//     "X-Shopify-Access-Token": "",
//   },
//   body: JSON.stringify({
//     query: `mutation updateOrderShippingAddress($input: OrderInput!) {
//       orderUpdate(input: $input) {
//         order {
//           id
//           shippingAddress {
//             address1
//             address2
//             city
//             countryCode
//             zip
//           }
//         }
//         userErrors {
//           message
//           field
//         }
//       }
//     }`,
//     variables: {
//       input: {
//         shippingAddress: {
//           address1: "496 Surabhi the royal",
//           address2: "pasodara patia",
//           city: "surat",
//           country: "India",
//           zip: "395006",
//         },
//         id: "gid://shopify/Order/6111898075323",
//       },
//     },
//   }),
// })
//   .then((response) => response.json())
//   .then((data) => console.log(data))
//   .catch((error) => console.error("Error:", error));
// const shopify = new ShopifyClient();
// shopify
//   .loadProducts(
//     "",
//     "miraiminds.myshopify.com",
//     null,
//     5,
//   )
//   .then((res) => console.log(res));
