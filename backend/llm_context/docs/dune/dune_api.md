# Dune Analytics API

Dune is a web-based platform that allows you to query public blockchain data and aggregate it into beautiful dashboards.

import { QueryParameter, DuneClient, RunQueryArgs } from "@duneanalytics/client-sdk";
const { DUNE_API_KEY } = process.env;

const client = new DuneClient(DUNE_API_KEY ?? "");
const queryId = 1215383;
const opts: RunQueryArgs = {
queryId,
query_parameters: [
QueryParameter.text("TextField", "Plain Text"),
QueryParameter.number("NumberField", 3.1415926535),
QueryParameter.date("DateField", "2022-05-04 00:00:00"),
QueryParameter.enum("ListField", "Option 1"),
],
};

client
.runQuery(opts)
.then((executionResult) => console.log(executionResult.result?.rows));

// should look like
// [
// {
// date_field: "2022-05-04 00:00:00.000",
// list_field: "Option 1",
// number_field: "3.1415926535",
// text_field: "Plain Text",
// },
// ]
